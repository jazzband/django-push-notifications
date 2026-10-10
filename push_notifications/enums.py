from enum import Enum


class InterruptionLevelType(str, Enum):
	PASSIVE = "passive"
	ACTIVE = "active"
	TIME_SENSITIVE = "time-sensitive"
	CRITICAL = "critical"
