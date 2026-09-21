import logging
from datetime import date, datetime, time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from poc20.application.lead_workflow import LeadWorkflow
from poc20.database import get_db
from poc20.domain.exceptions import (
    AppointmentError,
    InvalidWorkflowTransition,
)
from poc20.domain.models import (
    Appointment,
    ConversationMessage,
    LeadSession,
    WorkflowResult,
)
from poc20.infrastructure.calendar_client import (
    CalendarClient,
    MockCalendarClient,
)
from poc20.infrastructure.openai_client import (
    OpenAIClient,
    OpenAIClientError,
)
from poc20.infrastructure.repositories import (
    LeadRepository,
    MessageRepository,
)
from poc20.infrastructure.task_client import (
    MockTaskClient,
    TaskClient,
)
from poc20.services.appointment_service import (
    AppointmentService,
)
from poc20.services.lead_scorer import LeadScorer
from poc20.services.property_matcher import PropertyMatcher
from poc20.services.requirement_extractor import (
    RequirementExtractionError,
    RequirementExtractor,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/poc20",
    tags=["CRM Agent"],
)


class LeadMessageRequest(BaseModel):
    session_id: str = Field(
        min_length=1,
        max_length=100,
    )
    message: str = Field(
        min_length=1,
        max_length=5000,
    )


class AppointmentRequest(BaseModel):
    session_id: str = Field(
        min_length=1,
        max_length=100,
    )
    appointment_date: date
    appointment_time: time
    property_id: str | None = None
    idempotency_key: str = Field(
        min_length=1,
        max_length=255,
    )


class TaskRequest(BaseModel):
    session_id: str = Field(
        min_length=1,
        max_length=100,
    )
    title: str = Field(
        min_length=1,
        max_length=500,
    )
    due_at: datetime | None = None
    property_id: str | None = None
    idempotency_key: str = Field(
        min_length=1,
        max_length=255,
    )


def _load_properties() -> list[dict[str, Any]]:
    """
    Temporary property source for the POC API.

    This keeps the API independent from the existing CRM
    while the dedicated property repository is introduced.
    """

    return [
        {
            "property_id": "PROP-001",
            "location": "Hinjewadi",
            "property_type": "APARTMENT",
            "bedrooms": 2,
            "price_lakhs": 78,
        },
        {
            "property_id": "PROP-002",
            "location": "Hinjewadi",
            "property_type": "APARTMENT",
            "bedrooms": 2,
            "price_lakhs": 82,
        },
        {
            "property_id": "PROP-003",
            "location": "Wakad",
            "property_type": "APARTMENT",
            "bedrooms": 2,
            "price_lakhs": 75,
        },
        {
            "property_id": "PROP-004",
            "location": "Hinjewadi",
            "property_type": "APARTMENT",
            "bedrooms": 3,
            "price_lakhs": 95,
        },
        {
            "property_id": "PROP-005",
            "location": "Baner",
            "property_type": "APARTMENT",
            "bedrooms": 2,
            "price_lakhs": 88,
        },
    ]


def _build_workflow(
    db: Session,
) -> LeadWorkflow:

    try:
        llm_client = OpenAIClient()
    except OpenAIClientError:
        logger.warning(
            "OpenAI client is not configured."
        )
        raise

    lead_repository = LeadRepository(db)
    message_repository = MessageRepository(db)

    requirement_extractor = RequirementExtractor(
        llm_client=llm_client,
    )

    property_matcher = PropertyMatcher(
        properties=_load_properties(),
    )

    lead_scorer = LeadScorer()

    return LeadWorkflow(
        lead_repository=lead_repository,
        message_repository=message_repository,
        requirement_extractor=requirement_extractor,
        property_matcher=property_matcher,
        lead_scorer=lead_scorer,
    )


@router.get(
    "/health",
)
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "real-estate-crm-agent",
    }


@router.post(
    "/leads/message",
    response_model=WorkflowResult,
)
def process_lead_message(
    request: LeadMessageRequest,
    db: Session = Depends(get_db),
) -> WorkflowResult:

    try:
        workflow = _build_workflow(db)

        return workflow.process_message(
            session_id=request.session_id,
            message=request.message,
        )

    except RequirementExtractionError as exc:
        logger.warning(
            "Requirement extraction failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except OpenAIClientError as exc:
        logger.error(
            "AI service unavailable: %s",
            exc,
        )

        raise HTTPException(
            status_code=503,
            detail="AI service is currently unavailable.",
        ) from exc

    except InvalidWorkflowTransition as exc:
        logger.error(
            "Workflow transition failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Lead processing failed."
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to process lead message.",
        ) from exc


@router.get(
    "/leads/{session_id}",
    response_model=LeadSession,
)
def get_lead(
    session_id: str,
    db: Session = Depends(get_db),
) -> LeadSession:

    repository = LeadRepository(db)

    session = repository.get_by_session_id(
        session_id
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Lead session not found.",
        )

    return session


@router.get(
    "/leads/{session_id}/history",
    response_model=list[ConversationMessage],
)
def get_lead_history(
    session_id: str,
    db: Session = Depends(get_db),
) -> list[ConversationMessage]:

    repository = MessageRepository(db)

    history = repository.get_history(
        session_id
    )

    if not history:
        raise HTTPException(
            status_code=404,
            detail="Conversation history not found.",
        )

    return history


@router.post(
    "/appointments",
    response_model=Appointment,
)
def create_appointment(
    request: AppointmentRequest,
    db: Session = Depends(get_db),
) -> Appointment:

    lead_repository = LeadRepository(db)

    session = lead_repository.get_by_session_id(
        request.session_id
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Lead session not found.",
        )

    service = AppointmentService()

    try:
        appointment = service.validate(
            appointment_date=request.appointment_date,
            appointment_time=request.appointment_time,
            property_id=request.property_id,
        )

        calendar_client: CalendarClient = (
            MockCalendarClient(db)
        )

        start_time = datetime.combine(
            appointment.appointment_date,
            appointment.appointment_time,
        ).replace(
            tzinfo=service.timezone
        )

        from datetime import timedelta

        end_time = start_time + timedelta(
            minutes=60
        )

        calendar_client.create_event(
            title="Real Estate Property Visit",
            start_time=start_time,
            end_time=end_time,
            timezone=appointment.timezone,
            property_id=appointment.property_id,
            session_id=request.session_id,
            idempotency_key=request.idempotency_key,
        )

        appointment.confirmed = True

        session.appointment = appointment

        lead_repository.update(session)

        return appointment

    except AppointmentError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Appointment creation failed."
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to create appointment.",
        ) from exc


@router.post(
    "/tasks",
)
def create_task(
    request: TaskRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:

    lead_repository = LeadRepository(db)

    session = lead_repository.get_by_session_id(
        request.session_id
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Lead session not found.",
        )

    try:
        task_client: TaskClient = (
            MockTaskClient(db)
        )

        task = task_client.create_task(
            title=request.title,
            session_id=request.session_id,
            due_at=request.due_at,
            property_id=request.property_id,
            idempotency_key=request.idempotency_key,
        )

        return {
            "task_id": task.task_id,
            "title": task.title,
            "due_at": task.due_at,
            "session_id": task.session_id,
            "property_id": task.property_id,
            "status": task.status,
        }

    except Exception as exc:
        logger.exception(
            "Task creation failed."
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to create task.",
        ) from exc