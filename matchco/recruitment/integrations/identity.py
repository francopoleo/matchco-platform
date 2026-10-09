"""Identity integration contract and default implementation."""

from .defaults import NullIdentityAdapter
from .ports import IdentityPort

__all__ = ['IdentityPort', 'NullIdentityAdapter']
