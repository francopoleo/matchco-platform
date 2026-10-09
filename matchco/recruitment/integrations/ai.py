"""Optional AI matching integration; rules remain the fallback."""

from typing import Protocol


class AIMatchingPort(Protocol):
    def explain(self, *, candidate_id: int, position_id: int, features: dict) -> dict: ...


class NullAIMatchingAdapter:
    def explain(self, *, candidate_id: int, position_id: int, features: dict):
        return {'status': 'not_configured', 'factors': features}


__all__ = ['AIMatchingPort', 'NullAIMatchingAdapter']
