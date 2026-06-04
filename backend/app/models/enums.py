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

class OptimizationType(str, enum.Enum):
    """Types of resume optimizations."""
    KEYWORD = "KEYWORD"
    BULLET_REWRITE = "BULLET_REWRITE"
    SKILL_ADDITION = "SKILL_ADDITION"
    SUMMARY_IMPROVEMENT = "SUMMARY_IMPROVEMENT"
    ATS_FIX = "ATS_FIX"

class OptimizationStatus(str, enum.Enum):
    """Status of a proposed optimization."""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
