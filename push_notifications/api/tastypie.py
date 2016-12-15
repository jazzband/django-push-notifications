from __future__ import absolute_import

from tastypie.authorization import Authorization
from tastypie.authentication import BasicAuthentication
from tastypie.resources import ModelResource
from push_notifications.models import APNSDevice, GCMDevice, WNSDevice


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


class WNSDeviceResource(ModelResource):
	class Meta:
		authorization = Authorization()
		queryset = WNSDevice.objects.all()
		resource_name = "device/wns"


class APNSDeviceAuthenticatedResource(APNSDeviceResource):
	# user = ForeignKey(UserResource, "user")

	class Meta(APNSDeviceResource.Meta):
		authentication = BasicAuthentication()
	# authorization = SameUserAuthorization()

	def obj_create(self, bundle, **kwargs):
		# See https://github.com/toastdriven/django-tastypie/issues/854
		return super(APNSDeviceAuthenticatedResource, self).obj_create(bundle, user=bundle.request.user, **kwargs)


class GCMDeviceAuthenticatedResource(GCMDeviceResource):
	# user = ForeignKey(UserResource, "user")

	class Meta(GCMDeviceResource.Meta):
		authentication = BasicAuthentication()
	# authorization = SameUserAuthorization()

	def obj_create(self, bundle, **kwargs):
		# See https://github.com/toastdriven/django-tastypie/issues/854
		return super(GCMDeviceAuthenticatedResource, self).obj_create(bundle, user=bundle.request.user, **kwargs)


class WNSDeviceAuthenticatedResource(WNSDeviceResource):
	# user = ForeignKey(UserResource, "user")

	class Meta(WNSDeviceResource.Meta):
		authentication = BasicAuthentication()
	# authorization = SameUserAuthorization()

	def obj_create(self, bundle, **kwargs):
		# See https://github.com/toastdriven/django-tastypie/issues/854
		return super(WNSDeviceAuthenticatedResource, self).obj_create(bundle, user=bundle.request.user, **kwargs)
