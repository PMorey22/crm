import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from poc20.domain.entities import (
    IdempotencyEntity,
    LeadEntity,
    MessageEntity,
)
from poc20.domain.enums import LeadStage, MessageRole
from poc20.domain.models import (
    Appointment,
    ConversationMessage,
    LeadScore,
    LeadSession,
    Requirements,
)


class LeadRepository:
    """Persistence operations for lead sessions."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_session_id(
        self,
        session_id: str,
    ) -> LeadSession | None:
        entity = self.db.scalar(
            select(LeadEntity).where(
                LeadEntity.session_id == session_id
            )
        )

        if entity is None:
            return None

        requirements_data = json.loads(
            entity.requirements_json or "{}"
        )

        appointment_data = json.loads(
            entity.appointment_json or "{}"
        )

        lead_score = None

        if entity.lead_score is not None:
            lead_score = LeadScore(
                score=entity.lead_score,
                reasons=[],
            )

        return LeadSession(
            session_id=entity.session_id,
            stage=LeadStage(entity.stage),
            requirements=Requirements.model_validate(
                requirements_data
            ),
            appointment=Appointment.model_validate(
                appointment_data
            ),
            lead_score=lead_score,
        )

    def create(
        self,
        session: LeadSession,
    ) -> LeadSession:
        existing = self.get_by_session_id(
            session.session_id
        )

        if existing is not None:
            return existing

        entity = LeadEntity(
            session_id=session.session_id,
            stage=session.stage.value,
            requirements_json=session.requirements.model_dump_json(),
            appointment_json=session.appointment.model_dump_json(),
            lead_score=(
                session.lead_score.score
                if session.lead_score
                else None
            ),
        )

        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)

        return session

    def update(
        self,
        session: LeadSession,
    ) -> LeadSession:
        entity = self.db.scalar(
            select(LeadEntity).where(
                LeadEntity.session_id == session.session_id
            )
        )

        if entity is None:
            return self.create(session)

        entity.stage = session.stage.value

        entity.requirements_json = (
            session.requirements.model_dump_json()
        )

        entity.appointment_json = (
            session.appointment.model_dump_json()
        )

        entity.lead_score = (
            session.lead_score.score
            if session.lead_score
            else None
        )

        entity.updated_at = datetime.utcnow()

        self.db.commit()

        return session


class MessageRepository:
    """Persistence operations for conversation messages."""

    def __init__(self, db: Session):
        self.db = db

    def add(
        self,
        message: ConversationMessage,
    ) -> ConversationMessage:
        entity = MessageEntity(
            session_id=message.session_id,
            role=message.role.value,
            content=message.content,
            created_at=message.created_at,
        )

        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)

        return message

    def get_history(
        self,
        session_id: str,
    ) -> list[ConversationMessage]:
        entities = self.db.scalars(
            select(MessageEntity)
            .where(
                MessageEntity.session_id == session_id
            )
            .order_by(MessageEntity.created_at)
        ).all()

        return [
            ConversationMessage(
                session_id=entity.session_id,
                role=MessageRole(entity.role),
                content=entity.content,
                created_at=entity.created_at,
            )
            for entity in entities
        ]


class IdempotencyRepository:
    """Prevents duplicate external operations."""

    def __init__(self, db: Session):
        self.db = db

    def get(
        self,
        idempotency_key: str,
    ) -> IdempotencyEntity | None:
        return self.db.scalar(
            select(IdempotencyEntity).where(
                IdempotencyEntity.idempotency_key
                == idempotency_key
            )
        )

    def exists(
        self,
        idempotency_key: str,
    ) -> bool:
        return self.get(idempotency_key) is not None

    def save(
        self,
        idempotency_key: str,
        operation: str,
        resource_id: str | None = None,
    ) -> IdempotencyEntity:
        existing = self.get(idempotency_key)

        if existing is not None:
            return existing

        entity = IdempotencyEntity(
            idempotency_key=idempotency_key,
            operation=operation,
            resource_id=resource_id,
        )

        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)

        return entity