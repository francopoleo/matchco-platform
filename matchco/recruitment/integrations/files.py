"""Optional resume/file storage integration."""

from .defaults import NullFileAdapter
from .ports import FilePort

__all__ = ['FilePort', 'NullFileAdapter']
