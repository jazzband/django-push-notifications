from tastypie.authorization import Authorization
from tastypie.resources import ModelResource
from .models import APNSDevice, GCMDevice


class APNSDeviceResource(ModelResource):
	class Meta:
		authorization = Authorization()
		queryset = APNSDevice.objects.all()
		resource_name = "device/apns"

class GCMDeviceResource(ModelResource):
	class Meta:
		authorization = Authorization()
		queryset = GCMDevice.objects.all()
		resource_name = "device/gcm"
