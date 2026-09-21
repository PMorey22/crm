from enum import Enum


class LeadStage(str, Enum):
    NEW = "NEW"
    QUALIFYING = "QUALIFYING"
    QUALIFIED = "QUALIFIED"
    MATCHED = "MATCHED"
    APPOINTMENT = "APPOINTMENT"
    APPOINTMENT_CONFIRMATION = "APPOINTMENT_CONFIRMATION"
    COMPLETED = "COMPLETED"


class PropertyType(str, Enum):
    APARTMENT = "APARTMENT"
    VILLA = "VILLA"
    PLOT = "PLOT"
    HOUSE = "HOUSE"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"from enum import Enum


class LeadStage(str, Enum):
    NEW = "NEW"
    QUALIFYING = "QUALIFYING"
    QUALIFIED = "QUALIFIED"
    MATCHED = "MATCHED"
    APPOINTMENT = "APPOINTMENT"
    APPOINTMENT_CONFIRMATION = "APPOINTMENT_CONFIRMATION"
    COMPLETED = "COMPLETED"


class PropertyType(str, Enum):
    APARTMENT = "APARTMENT"
    VILLA = "VILLA"
    PLOT = "PLOT"
    HOUSE = "HOUSE"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"