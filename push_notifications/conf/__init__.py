from django.utils.module_loading import import_string

from .app import AppConfig  # noqa: F401
from .appmodel import AppModelConfig  # noqa: F401
from .legacy import LegacyConfig  # noqa: F401
from ..settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS  # noqa: I001


manager = None


def get_manager(reload=False):
	global manager

	if not manager or reload is True:
		manager = import_string(SETTINGS["CONFIG"])()

	return manager


# implementing get_manager as a function allows tests to reload settings
get_manager()
