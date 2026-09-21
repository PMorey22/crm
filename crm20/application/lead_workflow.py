from datetime import datetime, timezone

from poc20.domain.enums import LeadStage, MessageRole
from poc20.domain.exceptions import InvalidWorkflowTransition
from poc20.domain.models import (
    ConversationMessage,
    LeadSession,
    WorkflowResult,
)
from poc20.infrastructure.repositories import (
    LeadRepository,
    MessageRepository,
)
from poc20.services.lead_scorer import LeadScorer
from poc20.services.property_matcher import PropertyMatcher
from poc20.services.requirement_extractor import RequirementExtractor


ALLOWED_TRANSITIONS: dict[LeadStage, set[LeadStage]] = {
    LeadStage.NEW: {
        LeadStage.NEW,
        LeadStage.QUALIFYING,
    },
    LeadStage.QUALIFYING: {
        LeadStage.QUALIFYING,
        LeadStage.QUALIFIED,
    },
    LeadStage.QUALIFIED: {
        LeadStage.QUALIFIED,
        LeadStage.MATCHED,
    },
    LeadStage.MATCHED: {
        LeadStage.MATCHED,
        LeadStage.APPOINTMENT,
    },
    LeadStage.APPOINTMENT: {
        LeadStage.APPOINTMENT,
        LeadStage.APPOINTMENT_CONFIRMATION,
    },
    LeadStage.APPOINTMENT_CONFIRMATION: {
        LeadStage.APPOINTMENT_CONFIRMATION,
        LeadStage.COMPLETED,
    },
    LeadStage.COMPLETED: {
        LeadStage.COMPLETED,
    },
}


class LeadWorkflow:
    """
    Coordinates lead qualification, scoring and matching.
    """

    def __init__(
        self,
        lead_repository: LeadRepository,
        message_repository: MessageRepository,
        requirement_extractor: RequirementExtractor,
        property_matcher: PropertyMatcher,
        lead_scorer: LeadScorer,
    ):
        self.lead_repository = lead_repository
        self.message_repository = message_repository
        self.requirement_extractor = requirement_extractor
        self.property_matcher = property_matcher
        self.lead_scorer = lead_scorer

    def process_message(
        self,
        session_id: str,
        message: str,
    ) -> WorkflowResult:

        session = self._get_or_create_session(
            session_id
        )

        self._store_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=message,
        )

        requirements = (
            self.requirement_extractor.extract(
                message
            )
        )

        session.requirements = (
            self._merge_requirements(
                session.requirements,
                requirements,
            )
        )

        session.lead_score = (
            self.lead_scorer.calculate(
                session.requirements
            )
        )

        matches = self.property_matcher.find_matches(
            session.requirements,
            limit=5,
        )

        session.matched_properties = matches

        self._update_stage(
            session=session,
            matches_found=bool(matches),
        )

        self.lead_repository.update(session)

        response = self._build_response(session)

        self._store_message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=response,
        )

        return WorkflowResult(
            session_id=session.session_id,
            stage=session.stage,
            response=response,
            requirements=session.requirements,
            matches=matches,
            lead_score=session.lead_score,
            appointment=session.appointment,
        )

    def get_session(
        self,
        session_id: str,
    ) -> LeadSession | None:
        return self.lead_repository.get_by_session_id(
            session_id
        )

    def get_history(
        self,
        session_id: str,
    ) -> list[ConversationMessage]:
        return self.message_repository.get_history(
            session_id
        )

    def _get_or_create_session(
        self,
        session_id: str,
    ) -> LeadSession:

        existing = (
            self.lead_repository.get_by_session_id(
                session_id
            )
        )

        if existing:
            return existing

        session = LeadSession(
            session_id=session_id
        )

        return self.lead_repository.create(
            session
        )

    def _store_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
    ) -> None:

        self.message_repository.add(
            ConversationMessage(
                session_id=session_id,
                role=role,
                content=content,
                created_at=datetime.now(
                    timezone.utc
                ),
            )
        )

    @staticmethod
    def _merge_requirements(
        existing,
        extracted,
    ):
        data = existing.model_dump()

        extracted_data = extracted.model_dump(
            exclude_none=True
        )

        data.update(extracted_data)

        return type(existing).model_validate(
            data
        )

    def _update_stage(
        self,
        session: LeadSession,
        matches_found: bool,
    ) -> None:

        current_stage = session.stage

        if current_stage == LeadStage.COMPLETED:
            return

        if current_stage == LeadStage.NEW:
            self._transition(
                session,
                LeadStage.QUALIFYING,
            )

            current_stage = session.stage

        requirements = session.requirements

        fully_qualified = (
            requirements.location is not None
            and requirements.budget_lakhs is not None
            and (
                requirements.bedrooms is not None
                or requirements.property_type is not None
            )
        )

        if (
            current_stage == LeadStage.QUALIFYING
            and fully_qualified
        ):
            self._transition(
                session,
                LeadStage.QUALIFIED,
            )

            current_stage = session.stage

        if (
            current_stage == LeadStage.QUALIFIED
            and matches_found
        ):
            self._transition(
                session,
                LeadStage.MATCHED,
            )

    @staticmethod
    def _transition(
        session: LeadSession,
        target_stage: LeadStage,
    ) -> None:

        current_stage = session.stage

        allowed = ALLOWED_TRANSITIONS.get(
            current_stage,
            set(),
        )

        if target_stage not in allowed:
            raise InvalidWorkflowTransition(
                f"Invalid transition: "
                f"{current_stage.value} -> "
                f"{target_stage.value}"
            )

        session.stage = target_stage

    @staticmethod
    def _build_response(
        session: LeadSession,
    ) -> str:

        requirements = session.requirements
        matches = session.matched_properties

        missing: list[str] = []

        if not requirements.location:
            missing.append(
                "preferred location"
            )

        if requirements.budget_lakhs is None:
            missing.append("budget")

        if (
            requirements.bedrooms is None
            and requirements.property_type is None
        ):
            missing.append(
                "property type or BHK"
            )

        if missing:
            return (
                "I can help you find suitable "
                "properties. Please provide your "
                + ", ".join(missing)
                + "."
            )

        if matches:
            property_ids = ", ".join(
                match.property_id
                for match in matches[:3]
            )

            return (
                f"I found {len(matches)} matching "
                f"properties based on your requirements. "
                f"Top matches: {property_ids}. "
                "Would you like to schedule a "
                "property visit?"
            )

        return (
            "I have captured your requirements, "
            "but I couldn't find an exact property "
            "match yet. We can broaden the search "
            "criteria if you'd like."
        )