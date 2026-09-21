import pytest

from poc20.application.lead_workflow import (
    ALLOWED_TRANSITIONS,
    LeadWorkflow,
)
from poc20.domain.enums import LeadStage
from poc20.domain.exceptions import (
    InvalidWorkflowTransition,
)
from poc20.domain.models import LeadSession


def test_allowed_transition() -> None:
    session = LeadSession(
        session_id="test-1",
        stage=LeadStage.NEW,
    )

    assert (
        LeadStage.QUALIFYING
        in ALLOWED_TRANSITIONS[
            LeadStage.NEW
        ]
    )

    LeadWorkflow._transition(
        session,
        LeadStage.QUALIFYING,
    )

    assert session.stage == LeadStage.QUALIFYING


def test_invalid_transition() -> None:
    session = LeadSession(
        session_id="test-2",
        stage=LeadStage.NEW,
    )

    with pytest.raises(
        InvalidWorkflowTransition
    ):
        LeadWorkflow._transition(
            session,
            LeadStage.COMPLETED,
        )