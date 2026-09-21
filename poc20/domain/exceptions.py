class CRMPOCException(Exception):
  """Base exception for the CRM agent POC."""


class ValidationError(CRMPOCException):
  """Raised when input or extracted data is invalid."""


class InvalidWorkflowTransition(CRMPOCException):
  """Raised when a lead attempts an invalid stage transition."""


class PropertyMatchingError(CRMPOCException):
  """Raised when property matching cannot be completed."""


class AppointmentError(CRMPOCException):
  """Raised when appointment processing fails."""


class ExternalServiceError(CRMPOCException):
  """Raised when an external integration fails."""


class DuplicateOperationError(CRMPOCException):
  """Raised when an operation has already been completed."""class CRMPOCException(Exception):
  """Base exception for the CRM agent POC."""


class ValidationError(CRMPOCException):
  """Raised when input or extracted data is invalid."""


class InvalidWorkflowTransition(CRMPOCException):
  """Raised when a lead attempts an invalid stage transition."""


class PropertyMatchingError(CRMPOCException):
  """Raised when property matching cannot be completed."""


class AppointmentError(CRMPOCException):
  """Raised when appointment processing fails."""


class ExternalServiceError(CRMPOCException):
  """Raised when an external integration fails."""


class DuplicateOperationError(CRMPOCException):
  """Raised when an operation has already been completed."""