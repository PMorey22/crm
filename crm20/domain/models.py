from datetime import date, time, datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from .enums import LeadStage, MessageRole, PropertyType


class Requirements(BaseModel):
    model_config = ConfigDict(extra="ignore")

    location: str | None = None
    property_type: PropertyType | None = None
    bedrooms: int | None = Field(default=None, ge=0, le=20)
    budget_lakhs: float | None = Field(default=None, ge=0)
    timeline_months: int | None = Field(default=None, ge=0, le=240)


class Appointment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    appointment_date: date | None = None
    appointment_time: time | None = None
    timezone: str = "Asia/Kolkata"
    confirmed: bool = False
    property_id: str | None = None


class ExtractedAppointment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    appointment_requested: bool = False
    appointment_date: str | None = None
    appointment_time: str | None = None
    confirmed: bool = False


class PropertyMatch(BaseModel):
    property_id: str
    score: float = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)


class LeadScore(BaseModel):
    score: float = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)


class LeadSession(BaseModel):
    session_id: str
    stage: LeadStage = LeadStage.NEW
    requirements: Requirements = Field(default_factory=Requirements)
    appointment: Appointment = Field(default_factory=Appointment)
    lead_score: LeadScore | None = None
    matched_properties: list[PropertyMatch] = Field(default_factory=list)


class ConversationMessage(BaseModel):
    session_id: str
    role: MessageRole
    content: str
    created_at: datetime


class WorkflowResult(BaseModel):
    session_id: str
    stage: LeadStage
    response: str
    requirements: Requirements
    matches: list[PropertyMatch] = Field(default_factory=list)
    lead_score: LeadScore | None = None
    appointment: Appointment | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)from datetime import date, time, datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from .enums import LeadStage, MessageRole, PropertyType


class Requirements(BaseModel):
    model_config = ConfigDict(extra="ignore")

    location: str | None = None
    property_type: PropertyType | None = None
    bedrooms: int | None = Field(default=None, ge=0, le=20)
    budget_lakhs: float | None = Field(default=None, ge=0)
    timeline_months: int | None = Field(default=None, ge=0, le=240)


class Appointment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    appointment_date: date | None = None
    appointment_time: time | None = None
    timezone: str = "Asia/Kolkata"
    confirmed: bool = False
    property_id: str | None = None


class ExtractedAppointment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    appointment_requested: bool = False
    appointment_date: str | None = None
    appointment_time: str | None = None
    confirmed: bool = False


class PropertyMatch(BaseModel):
    property_id: str
    score: float = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)


class LeadScore(BaseModel):
    score: float = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)


class LeadSession(BaseModel):
    session_id: str
    stage: LeadStage = LeadStage.NEW
    requirements: Requirements = Field(default_factory=Requirements)
    appointment: Appointment = Field(default_factory=Appointment)
    lead_score: LeadScore | None = None
    matched_properties: list[PropertyMatch] = Field(default_factory=list)


class ConversationMessage(BaseModel):
    session_id: str
    role: MessageRole
    content: str
    created_at: datetime


class WorkflowResult(BaseModel):
    session_id: str
    stage: LeadStage
    response: str
    requirements: Requirements
    matches: list[PropertyMatch] = Field(default_factory=list)
    lead_score: LeadScore | None = None
    appointment: Appointment | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)