"""Small, serializable contracts shared by recruitment integrations."""

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class PersonRef:
    """Reference to a person without importing an authentication model."""

    external_id: str
    email: str = ''
    display_name: str = ''


@dataclass(frozen=True)
class AssessmentRequest:
    candidate_id: int
    assessment_id: str
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AssessmentResult:
    assessment_id: str
    status: str = 'pending'
    score: Optional[float] = None
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NotificationRequest:
    recipient: str
    subject: str
    body: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FileRef:
    external_id: str
    name: str
    content_type: str = ''
    url: str = ''
