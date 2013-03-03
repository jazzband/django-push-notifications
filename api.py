from tastypie.authorization import Authorization
from tastypie.resources import ModelResource
from .models import GCMDevice

class GCMDeviceResource(ModelResource):
	class Meta:
		authorization = Authorization()
		queryset = GCMDevice.objects.all()
		resource_name = "gcmdevice"
