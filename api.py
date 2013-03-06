from tastypie.authorization import Authorization
from tastypie.authentication import BasicAuthentication
from tastypie.fields import ForeignKey
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


class APNSDeviceAuthenticatedResource(APNSDeviceResource):
	# user = ForeignKey(UserResource, "user")

	class Meta(APNSDeviceResource.Meta):
		authentication = BasicAuthentication()
		# authorization = SameUserAuthorization()

	def obj_create(self, bundle, **kwargs):
		bundle.data["user_id"] = bundle.request.user.id
		return super(APNSDeviceAuthenticatedResource, self).obj_create(bundle, **kwargs)


class GCMDeviceAuthenticatedResource(GCMDeviceResource):
	# user = ForeignKey(UserResource, "user")

	class Meta(GCMDeviceResource.Meta):
		authentication = BasicAuthentication()
		# authorization = SameUserAuthorization()

	def obj_create(self, bundle, **kwargs):
		bundle.data["user_id"] = bundle.request.user.id
		return super(GCMDeviceAuthenticatedResource, self).obj_create(bundle, **kwargs)
