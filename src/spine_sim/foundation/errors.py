"""Structured M00 error and validation reporting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One actionable validation failure."""

    code: str
    path: str
    message: str
    source: str | None = None
    layer: str | None = None
    original_value: Any = None
    suggestion: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "path": self.path,
            "message": self.message,
            "source": self.source,
            "layer": self.layer,
            "original_value": self.original_value,
            "suggestion": self.suggestion,
        }


class FoundationError(RuntimeError):
    """Base class for a classified M00 failure."""

    code = "FOUNDATION_ERROR"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class AggregateValidationError(FoundationError):
    """All validation issues found in one boundary pass."""

    code = "CONFIG_VALIDATION_FAILED"

    def __init__(self, issues: list[ValidationIssue] | tuple[ValidationIssue, ...]) -> None:
        self.issues = tuple(issues)
        super().__init__(
            f"validation failed with {len(self.issues)} issue(s)",
            details={"issues": [issue.as_dict() for issue in self.issues]},
        )


class ContractViolation(FoundationError):
    code = "CONTRACT_VIOLATION"


class SchemaRegistrationError(FoundationError):
    code = "SCHEMA_REGISTRATION_ERROR"


class TransactionError(FoundationError):
    code = "TRANSACTION_ERROR"


class IdempotencyConflict(TransactionError):
    code = "IDEMPOTENCY_KEY_CONFLICT"


class IntegrityError(FoundationError):
    code = "INTEGRITY_ERROR"


class CompatibilityError(FoundationError):
    code = "SCHEMA_COMPATIBILITY_ERROR"


class QueryError(FoundationError):
    code = "QUERY_ERROR"
