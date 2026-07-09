import logging

from django.db import IntegrityError
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from rest_framework import permissions, status
from rest_framework.fields import IntegerField
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer, ValidationError
from rest_framework.viewsets import ModelViewSet

from push_notifications.fields import UNSIGNED_64BIT_INT_MAX_VALUE, hex_re
from push_notifications.models import APNSDevice, GCMDevice, WebPushDevice, WNSDevice
from push_notifications.settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS
from typing import Any, Union, Dict, Optional


# Fields
class HexIntegerField(IntegerField):
	"""
	Store an integer represented as a hex string of form "0x01".
	"""

	def to_internal_value(self, data: Union[str, int]) -> int:
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
			"id",
			"name",
			"application_id",
			"registration_id",
			"device_id",
			"active",
			"date_created",
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
	def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
		devices: Optional[Any] = None
		primary_key: Optional[Any] = None
		request_method: Optional[str] = None

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
			reg_id: str = attrs.get("registration_id", self.instance.registration_id)
			devices = Device.objects.filter(registration_id=reg_id).exclude(
				id=primary_key
			)
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
		allow_null=True,
	)

	class Meta(DeviceSerializerMixin.Meta):
		model = GCMDevice
		fields = (
			"id",
			"name",
			"registration_id",
			"device_id",
			"active",
			"date_created",
			"cloud_message_type",
			"application_id",
		)
		extra_kwargs = {"id": {"read_only": False, "required": False}}

	def validate_device_id(self, value: Optional[int] = None) -> Optional[int]:
		# device ids are 64 bit unsigned values
		if value is not None and value > UNSIGNED_64BIT_INT_MAX_VALUE:
			raise ValidationError("Device ID is out of range")
		return value


class WNSDeviceSerializer(UniqueRegistrationSerializerMixin, ModelSerializer):
	class Meta(DeviceSerializerMixin.Meta):
		model = WNSDevice


class WebPushDeviceSerializer(UniqueRegistrationSerializerMixin, ModelSerializer):
	class Meta(DeviceSerializerMixin.Meta):
		model = WebPushDevice
		fields = (
			"id",
			"name",
			"registration_id",
			"active",
			"date_created",
			"p256dh",
			"auth",
			"browser",
			"application_id",
		)


# Permissions
class IsOwner(permissions.BasePermission):
	def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
		# must be the owner to view the object
		return obj.user == request.user


# Mixins
class DeviceViewSetMixin:
	lookup_field: str = "registration_id"

	def create(self, request: Any, *args: Any, **kwargs: Any) -> Response:
		serializer: Optional[Any] = None
		is_update: bool = False
		if (
			SETTINGS.get("UPDATE_ON_DUPLICATE_REG_ID")
			and self.lookup_field in request.data
		):
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
			try:
				self.perform_create(serializer)
			except IntegrityError:
				instance = self.queryset.model.objects.filter(
					registration_id=request.data[self.lookup_field]
				).first()
				if instance:
					logger.error(f"registration_id already exist {instance.registration_id} user: {instance.user} created time for that {instance.date_created}", exc_info=True)
				else:
					logger.error(f"registration_id that already exist {instance}", exc_info=True)
			headers = self.get_success_headers(serializer.data)
			return Response(
				serializer.data, status=status.HTTP_201_CREATED, headers=headers
			)

	def perform_create(self, serializer: Serializer) -> Any:
		if self.request.user.is_authenticated:
			serializer.save(user=self.request.user)
		return super().perform_create(serializer)

	def perform_update(self, serializer: Serializer) -> Any:
		if self.request.user.is_authenticated:
			serializer.save(user=self.request.user)
		return super().perform_update(serializer)


class CustomDeviceViewSetMixin:
	lookup_field = "registration_id"

	def create(self, request, *args, **kwargs):
		serializer = None
		is_update = False
		log_error = False

		if SETTINGS.get("UPDATE_ON_DUPLICATE_REG_ID") and self.lookup_field in request.data:
			old_registration_id = request.data.get("old_registration_id", None)
			new_registration_id = request.data.get("registration_id", None)
			if new_registration_id and not old_registration_id:
				instance = self.queryset.model.objects.filter(
					registration_id=new_registration_id
				).first()
				if instance:
					serializer = self.get_serializer(instance, data=request.data)
					is_update = True
				if not serializer:
					serializer = self.get_serializer(data=request.data)
			elif new_registration_id and old_registration_id:
				instance = self.queryset.model.objects.filter(
					registration_id=old_registration_id
				).first()
				if instance:
					serializer = self.get_serializer(instance, data=request.data)
					is_update = True
				if not serializer:
					serializer = self.get_serializer(data=request.data)
					log_error = True

		serializer.is_valid(raise_exception=True)
		if is_update:
			self.perform_update(serializer)
			return Response(serializer.data)
		else:
			self.perform_create(serializer, log_error=log_error)
			headers = self.get_success_headers(serializer.data)
			return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

	def perform_create(self, serializer, log_error=False):
		if self.request.user.is_authenticated:
			serializer.save(user=self.request.user)
			if log_error:
				logger.error(
					f"No device found against old_registration_id created with new registration_id. User:{self.request.user.id}",
					exc_info=True)
		return super(CustomDeviceViewSetMixin, self).perform_create(serializer)

	def perform_update(self, serializer):
		if self.request.user.is_authenticated:
			serializer.save(user=self.request.user)
		return super(CustomDeviceViewSetMixin, self).perform_update(serializer)


class AuthorizedMixin:
	permission_classes: tuple = (permissions.IsAuthenticated, IsOwner)

	def get_queryset(self) -> Any:
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


class CustomGCMDeviceViewSet(CustomDeviceViewSetMixin, ModelViewSet):
	queryset = GCMDevice.objects.all()
	serializer_class = GCMDeviceSerializer


class GCMDeviceAuthorizedViewSet(AuthorizedMixin, GCMDeviceViewSet):
	pass


class CustomGCMDeviceAuthorizedViewSet(AuthorizedMixin, CustomGCMDeviceViewSet):
	pass


class WNSDeviceViewSet(DeviceViewSetMixin, ModelViewSet):
	queryset = WNSDevice.objects.all()
	serializer_class = WNSDeviceSerializer


class WNSDeviceAuthorizedViewSet(AuthorizedMixin, WNSDeviceViewSet):
	pass


class WebPushDeviceViewSet(DeviceViewSetMixin, ModelViewSet):
	queryset = WebPushDevice.objects.all()
	serializer_class = WebPushDeviceSerializer
	lookup_value_regex: str = ".+"


class WebPushDeviceAuthorizedViewSet(AuthorizedMixin, WebPushDeviceViewSet):
	pass
