from __future__ import absolute_import

import re

from rest_framework import permissions
from rest_framework.serializers import ModelSerializer, ValidationError
from rest_framework.viewsets import ModelViewSet

from push_notifications.models import APNSDevice, GCMDevice

HEX64_RE = re.compile("[0-9a-f]{64}", re.IGNORE_CASE)


# Serializers
class APNSDeviceSerializer(ModelSerializer):
	class Meta:
		model = APNSDevice

	def validate_registration_id(self, attrs, source):
		# iOS device tokens are 256-bit hexadecimal (64 characters)

		if HEX64_RE.match(attrs[source]) is None:
			raise ValidationError("Registration ID (device token) is invalid")
		return attrs


class GCMDeviceSerializer(ModelSerializer):
	class Meta:
		model = GCMDevice


# Permissions
class IsOwnerOrReadOnly(permissions.BasePermission):
	def has_object_permission(self, request, view, obj):
		# Read permissions are allowed to any safe request (GET, HEAD or OPTIONS)
		if request.method in permissions.SAFE_METHODS:
			return True

		return obj.user == request.user


# Mixins
class DeviceMixin(object):
	def pre_save(self, obj):
		if self.request.user.is_authenticated():
			obj.user = self.request.user


class AuthorizedMixin(object):
	permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly)


# ViewSets
class APNSDeviceViewSet(DeviceMixin, ModelViewSet):
	queryset = APNSDevice.objects.all()
	serializer_class = APNSDeviceSerializer


class APNSDeviceAuthorizedViewSet(AuthorizedMixin, APNSDeviceViewSet):
	pass


class GCMDeviceViewSet(DeviceMixin, ModelViewSet):
	queryset = GCMDevice.objects.all()
	serializer_class = GCMDeviceSerializer


class GCMDeviceAuthorizedViewSet(AuthorizedMixin, GCMDeviceViewSet):
	pass
