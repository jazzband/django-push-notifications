from django.conf import settings

if "tastypie" in settings.INSTALLED_APPS:
	# Tastypie resources are importable from the api package level (backwards compatibility)
	from .tastypie import APNSDeviceResource, GCMDeviceResource, APNSDeviceAuthenticatedResource, GCMDeviceAuthenticatedResource

	__all__ = [
		"APNSDeviceResource",
		"GCMDeviceResource",
		"APNSDeviceAuthenticatedResource",
		"GCMDeviceAuthenticatedResource"
	]
