from django.conf import settings

if "tastypie" in settings.INSTALLED_APPS:
	# Tastypie resources are importable from the api package level (backwards compatibility)
	from .tastypie import APNSDeviceResource, GCMDeviceResource, WNSDeviceResource, APNSDeviceAuthenticatedResource, \
		GCMDeviceAuthenticatedResource, WNSDeviceAuthenticatedResource

	__all__ = [
		"APNSDeviceResource",
		"GCMDeviceResource",
		"WNSDeviceResource",
		"APNSDeviceAuthenticatedResource",
		"GCMDeviceAuthenticatedResource",
		"WNSDeviceAuthenticatedResource",
	]
