from django.utils.module_loading import import_string
from ..settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS
from typing import Union, Optional
from .app import AppConfig
from .appmodel import AppModelConfig
from .legacy import LegacyConfig

# ManagerType is an alias for the possible configuration manager classes
# that can be loaded dynamically via SETTINGS["CONFIG"].
ManagerType = Union[AppConfig, AppModelConfig, LegacyConfig]

manager: Optional[ManagerType] = None


def get_manager(reload: bool = False) -> ManagerType:
	global manager
	if not manager or reload:
		manager = import_string(SETTINGS["CONFIG"])()
	return manager


# implementing get_manager as a function allows tests to reload settings
get_manager()
