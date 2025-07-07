from rest_framework import permissions, status
from rest_framework.fields import IntegerField
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer, ValidationError
from rest_framework.viewsets import ModelViewSet
from typing import Any
from push_notifications.fields import UNSIGNED_64BIT_INT_MAX_VALUE, hex_re
from push_notifications.models import APNSDevice, GCMDevice, WebPushDevice, WNSDevice
from push_notifications.settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS
from django.db.models import QuerySet


# Fields
class HexIntegerField(IntegerField):
	"""
	Store an integer represented as a hex string of form "0x01".
	"""

	def to_internal_value(self, data: str | int) -> int:
		# validate hex string and convert it to the unsigned
		# integer representation for internal use
		try:
			data = int(data, 16) if not isinstance(data, int) else data
		except ValueError:
			raise ValidationError("Device ID is not a valid hex number")
		return super().to_internal_value(data)

	def to_representation(self, value: int) -> int:
		return value


# Serializers
class DeviceSerializerMixin(ModelSerializer):
	class Meta:
		fields = (
			"id", "name", "application_id", "registration_id", "device_id",
			"active", "date_created"
		)
		read_only_fields = ("date_created",)

		# See https://github.com/tomchristie/django-rest-framework/issues/1101
		extra_kwargs = {"active": {"default": True}}


class APNSDeviceSerializer(ModelSerializer):
	class Meta(DeviceSerializerMixin.Meta):
		model = APNSDevice

	def validate_registration_id(self, value: str) -> str:

		# https://developer.apple.com/documentation/uikit/uiapplicationdelegate/1622958-application
		# As of 02/2023 APNS tokens (registration_id) "are of variable length. Do not hard-code their size."
		if hex_re.match(value) is None:
			raise ValidationError("Registration ID (device token) is invalid")

		return value


class UniqueRegistrationSerializerMixin(Serializer):
	def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
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
		if request_method == "update":
			reg_id = attrs.get("registration_id", self.instance.registration_id)
			devices = Device.objects.filter(registration_id=reg_id) \
				.exclude(id=primary_key)
		elif request_method == "create":
			devices = Device.objects.filter(registration_id=attrs["registration_id"])

		if devices:
			raise ValidationError({"registration_id": "This field must be unique."})
		return attrs


class GCMDeviceSerializer(UniqueRegistrationSerializerMixin, ModelSerializer):
	device_id = HexIntegerField(
		help_text="ANDROID_ID / TelephonyManager.getDeviceId() (e.g: 0x01)",
		style={"input_type": "text"},
		required=False,
		allow_null=True
	)

	class Meta(DeviceSerializerMixin.Meta):
		model = GCMDevice
		fields = (
			"id", "name", "registration_id", "device_id", "active", "date_created",
			"cloud_message_type", "application_id",
		)
		extra_kwargs = {"id": {"read_only": False, "required": False}}

	def validate_device_id(self, value: int) -> int:
		# device ids are 64 bit unsigned values
		if value > UNSIGNED_64BIT_INT_MAX_VALUE:
			raise ValidationError("Device ID is out of range")
		return value


class WNSDeviceSerializer(UniqueRegistrationSerializerMixin, ModelSerializer):
	class Meta(DeviceSerializerMixin.Meta):
		model = WNSDevice


class WebPushDeviceSerializer(UniqueRegistrationSerializerMixin, ModelSerializer):
	class Meta(DeviceSerializerMixin.Meta):
		model = WebPushDevice
		fields = (
			"id", "name", "registration_id", "active", "date_created",
			"p256dh", "auth", "browser", "application_id",
		)


# Permissions
class IsOwner(permissions.BasePermission):
	def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
		# must be the owner to view the object
		return obj.user == request.user


# Mixins
class DeviceViewSetMixin:
	lookup_field = "registration_id"

	def create(self, request: Any, *args: Any, **kwargs: Any) -> Response:
		serializer = None
		is_update = False
		if SETTINGS.get("UPDATE_ON_DUPLICATE_REG_ID") and self.lookup_field in request.data:
			instance = self.queryset.model.objects.filter(
				registration_id=request.data[self.lookup_field]
			).first()
			if instance:
				serializer = self.get_serializer(instance, data=request.data)
				is_update = True
		if not serializer:
			serializer = self.get_serializer(data=request.data)

		serializer.is_valid(raise_exception=True)
		if is_update:
			self.perform_update(serializer)
			return Response(serializer.data)
		else:
			self.perform_create(serializer)
			headers = self.get_success_headers(serializer.data)
			return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

	def perform_create(self, serializer: ModelSerializer) -> None:
		if self.request.user.is_authenticated:
			serializer.save(user=self.request.user)
		return super().perform_create(serializer)

	def perform_update(self, serializer: ModelSerializer) -> None:
		if self.request.user.is_authenticated:
			serializer.save(user=self.request.user)
		return super().perform_update(serializer)


class AuthorizedMixin:
	permission_classes = (permissions.IsAuthenticated, IsOwner)

	def get_queryset(self) -> QuerySet:
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


class WebPushDeviceViewSet(DeviceViewSetMixin, ModelViewSet):
	queryset = WebPushDevice.objects.all()
	serializer_class = WebPushDeviceSerializer


class WebPushDeviceAuthorizedViewSet(AuthorizedMixin, WebPushDeviceViewSet):
	pass
