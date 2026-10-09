"""Ports used by recruitment. Implementations must fail soft for optionals."""

from typing import Protocol

from .contracts import (
    AssessmentRequest,
    AssessmentResult,
    FileRef,
    NotificationRequest,
    PersonRef,
)


class IdentityPort(Protocol):
    def resolve_person(self, *, email: str, cpf: str = '') -> PersonRef | None: ...

    def register_candidate(self, *, candidate_id: int, email: str) -> PersonRef | None: ...


class AssessmentPort(Protocol):
    def request(self, request: AssessmentRequest) -> AssessmentResult: ...


class NotificationPort(Protocol):
    def send(self, request: NotificationRequest) -> bool: ...


class FilePort(Protocol):
    def store(self, *, name: str, content_type: str, content: bytes) -> FileRef: ...

    def delete(self, file_ref: FileRef) -> bool: ...
