from tastypie.authorization import Authorization
from tastypie.resources import ModelResource
from .models import APNSDevice, GCMDevice


class APNSDeviceResource(ModelResource):
	class Meta:
		authorization = Authorization()
		queryset = APNSDevice.objects.all()
		resource_name = "apnsdevice"

class GCMDeviceResource(ModelResource):
	class Meta:
		authorization = Authorization()
		queryset = GCMDevice.objects.all()
		resource_name = "gcmdevice"
