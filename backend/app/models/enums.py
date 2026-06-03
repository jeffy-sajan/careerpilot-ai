"""
Database Enums.
"""
import enum

class ApplicationStatus(str, enum.Enum):
    """Job application lifecycle statuses."""
    SAVED = "SAVED"
    APPLIED = "APPLIED"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    REJECTED = "REJECTED"

class ApplicationSource(str, enum.Enum):
    """Where the job application originated."""
    LINKEDIN = "LINKEDIN"
    NAUKRI = "NAUKRI"
    INDEED = "INDEED"
    COMPANY_WEBSITE = "COMPANY_WEBSITE"
    REFERRAL = "REFERRAL"
    OTHER = "OTHER"

class ResumeStatus(str, enum.Enum):
    """Resume upload and parsing statuses."""
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

