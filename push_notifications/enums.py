"""
Enumeration Types for public-facing interfaces.

This module contains enumeration types that are used in public-facing and underlying interfaces of the package -
such as the `InterruptionLevel` of Apple's User Notification System and others.

Created: 2024-03-27 14:13
"""

from enum import Enum, StrEnum


class InterruptionLevel(Enum):
    """
    Enumeration of the interruption levels of Apple's User Notification System.

    The interruption levels are used to determine the priority of a notification and the way (delivery timing) it is displayed to the user.

        Ref: https://developer.apple.com/documentation/usernotifications/unnotificationinterruptionlevel
    """

    # The notification is displayed as an alert.
    ACTIVE = 0

    # The notification is displayed as a time-sensitive alert.
    #
    # Time-sensitive alerts are displayed immediately,
    # even when the device is in Do Not Disturb mode or the notification is set to be delivered silently.
    TIME_SENSITIVE = 1

    # The notification is displayed as a critical alert.
    # Bypasses the Do Not Disturb mode and the silent mode to deliver the notification.
    CRITICAL_ALERT = 2

    # The notification is displayed as a passive notification.
    # Pushes the notification to the Notification Center (or list), essentially making it a silent notification.
    PASSIVE = 3
