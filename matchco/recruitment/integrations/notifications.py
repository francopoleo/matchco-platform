"""Optional notification integration."""

from .defaults import NullNotificationAdapter
from .ports import NotificationPort

__all__ = ['NotificationPort', 'NullNotificationAdapter']
