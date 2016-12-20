from __future__ import absolute_import

from rest_framework import permissions
from rest_framework.serializers import Serializer, ModelSerializer, ValidationError, CharField
from rest_framework.viewsets import ModelViewSet
from rest_framework.fields import IntegerField

from push_notifications.models import APNSDevice, GCMDevice, WNSDevice
from push_notifications.fields import hex_re
from push_notifications.fields import UNSIGNED_64BIT_INT_MAX_VALUE


# Serializers
class DeviceSerializerMixin(ModelSerializer):
	class Meta:
		fields = ("id", "name", "registration_id", "device_id", "active", "date_created")
		read_only_fields = ("date_created",)

		# See https://github.com/tomchristie/django-rest-framework/issues/1101
		extra_kwargs = {"active": {"default": True}}


class APNSDeviceSerializer(ModelSerializer):
	class Meta(DeviceSerializerMixin.Meta):
		model = APNSDevice

	def validate_registration_id(self, value):
		# iOS device tokens are 256-bit hexadecimal (64 characters). In 2016 Apple is increasing
		# iOS device tokens to 100 bytes hexadecimal (200 characters).

		if hex_re.match(value) is None or len(value) not in (64, 200):
			raise ValidationError("Registration ID (device token) is invalid")

		return value


class UniqueRegistrationSerializerMixin(Serializer):
	def validate(self, attrs):
		devices = None
		primary_key = None
		request_method = None
		if self.initial_data.get("registration_id", None):
			if self.instance:
				request_method = "update"
				primary_key = self.instance.id
			else:
				request_method = "create"
		else:
			if self.context["request"].method in ["PUT", "PATCH"]:
				request_method = "update"
				primary_key = self.instance.id
			elif self.context["request"].method == "POST":
				request_method = "create"

		Device = self.Meta.model
		if request_method == "update" and "registration_id" in attrs:
			devices = Device.objects.filter(registration_id=attrs["registration_id"]) \
				.exclude(id=primary_key)
		elif request_method == "create":
			devices = Device.objects.filter(registration_id=attrs["registration_id"])

		if devices:
			raise ValidationError({'registration_id': 'This field must be unique.'})
		return attrs


class GCMDeviceSerializer(UniqueRegistrationSerializerMixin, ModelSerializer):
	device_id = CharField(
		help_text="ANDROID_ID / TelephonyManager.getDeviceId() (e.g: 0x01)",
		style={"input_type": "text"},
		required=False,
		allow_null=True
	)

	class Meta(DeviceSerializerMixin.Meta):
		model = GCMDevice
		fields = (
			"id", "name", "registration_id", "device_id", "active", "date_created",
			"cloud_message_type",
		)
		extra_kwargs = {"id": {"read_only": False, "required": False}}


class WNSDeviceSerializer(UniqueRegistrationSerializerMixin, ModelSerializer):
	class Meta(DeviceSerializerMixin.Meta):
		model = WNSDevice


# Permissions
class IsOwner(permissions.BasePermission):
	def has_object_permission(self, request, view, obj):
		# must be the owner to view the object
		return obj.user == request.user


# Mixins
class DeviceViewSetMixin(object):
	lookup_field = "registration_id"

	def perform_create(self, serializer):
		if self.request.user.is_authenticated():
			serializer.save(user=self.request.user)
		return super(DeviceViewSetMixin, self).perform_create(serializer)

	def perform_update(self, serializer):
		# if the validated_data contains the id, a create will be perfomed so
		# pop the id if it is present
		if 'id' in serializer.validated_data:
			serializer.validated_data.pop('id')
		if self.request.user.is_authenticated():
			serializer.save(user=self.request.user)
		return super(DeviceViewSetMixin, self).perform_update(serializer)


class AuthorizedMixin(object):
	permission_classes = (permissions.IsAuthenticated, IsOwner)

	def get_queryset(self):
		# filter all devices to only those belonging to the current user
		return self.queryset.filter(user=self.request.user)


# ViewSets
class APNSDeviceViewSet(DeviceViewSetMixin, ModelViewSet):
	queryset = APNSDevice.objects.all()
	serializer_class = APNSDeviceSerializer


class APNSDeviceAuthorizedViewSet(AuthorizedMixin, APNSDeviceViewSet):
	pass


class GCMDeviceViewSet(DeviceViewSetMixin, ModelViewSet):
	queryset = GCMDevice.objects.all()
	serializer_class = GCMDeviceSerializer


class GCMDeviceAuthorizedViewSet(AuthorizedMixin, GCMDeviceViewSet):
	pass


class WNSDeviceViewSet(DeviceViewSetMixin, ModelViewSet):
	queryset = WNSDevice.objects.all()
	serializer_class = WNSDeviceSerializer


class WNSDeviceAuthorizedViewSet(AuthorizedMixin, WNSDeviceViewSet):
	pass
