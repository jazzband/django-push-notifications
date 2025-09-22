from django.apps import apps
from django.contrib import admin, messages
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from .exceptions import APNSServerError, GCMError, WebPushError
from .models import APNSDevice, GCMDevice, WebPushDevice, WNSDevice
from .settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS
from django.http import HttpRequest
from django.db.models import QuerySet


User = apps.get_model(*SETTINGS["USER_MODEL"].split("."))


class DeviceAdmin(admin.ModelAdmin):
	list_display = ("__str__", "device_id", "user", "active", "date_created")
	list_filter = ("active",)
	actions = ("send_message", "send_bulk_message", "enable", "disable")
	raw_id_fields = ("user",)

	if hasattr(User, "USERNAME_FIELD"):
		search_fields = ("name", "device_id", "user__%s" % (User.USERNAME_FIELD))
	else:
		search_fields = ("name", "device_id", "")

	def send_messages(self, request: HttpRequest, queryset: QuerySet, bulk: bool = False) -> None:
		"""
		Provides error handling for DeviceAdmin send_message and send_bulk_message methods.
		"""
		ret = []
		errors = []
		r = ""

		for device in queryset:
			try:
				if bulk:
					r = queryset.send_message("Test bulk notification")
				else:
					r = device.send_message("Test single notification")
				if r:
					ret.append(r)
			except GCMError as e:
				errors.append(str(e))
			except APNSServerError as e:
				errors.append(e.status)
			except WebPushError as e:
				errors.append(force_str(e))

			if bulk:
				break

		# Because NotRegistered and InvalidRegistration do not throw GCMError
		# catch them here to display error msg.
		if not bulk:
			for r in ret:
				if "error" in r["results"][0]:
					errors.append(r["results"][0]["error"])
		else:
			if "results" in ret[0][0]:
				try:
					errors = [r["error"] for r in ret[0][0]["results"] if "error" in r]
				except TypeError:
					for entry in ret[0][0]:
						errors = errors + [r["error"] for r in entry["results"] if "error" in r]
				except IndexError:
					pass
			else:
				# different format, e.g.:
				# [{'some_token1': 'Success',
				#  'some_token2': 'BadDeviceToken'}]
				for key, value in ret[0][0].items():
					if value.lower() != "success":
						errors.append(value)
		if errors:
			self.message_user(
				request, _("Some messages could not be processed: %r" % (", ".join(errors))),
				level=messages.ERROR
			)
		if ret:
			if bulk:
				# When the queryset exceeds the max_recipients value, the
				# send_message method returns a list of dicts, one per chunk
				if "results" in ret[0][0]:
					try:
						success = ret[0][0]["success"]
					except TypeError:
						success = 0
						for entry in ret[0][0]:
							success = success + entry["success"]
					if success == 0:
						return
				else:
					# different format, e.g.:
					# [{'some_token1': 'Success',
					#  'some_token2': 'BadDeviceToken'}]
					success = []
					for key, value in ret[0][0].items():
						if value.lower() == "success":
							success.append(key)

			elif len(errors) == len(ret):
				return
			if errors:
				msg = _("Some messages were sent: %s" % (ret))
			else:
				msg = _("All messages were sent: %s" % (ret))
			self.message_user(request, msg)

	def send_message(self, request: HttpRequest, queryset: QuerySet) -> None:
		self.send_messages(request, queryset)

	send_message.short_description = _("Send test message")

	def send_bulk_message(self, request: HttpRequest, queryset: QuerySet) -> None:
		self.send_messages(request, queryset, True)

	send_bulk_message.short_description = _("Send test message in bulk")

	def enable(self, request: HttpRequest, queryset: QuerySet) -> None:
		queryset.update(active=True)

	enable.short_description = _("Enable selected devices")

	def disable(self, request: HttpRequest, queryset: QuerySet) -> None:
		queryset.update(active=False)

	disable.short_description = _("Disable selected devices")


class GCMDeviceAdmin(DeviceAdmin):
	list_display = (
		"__str__", "device_id", "user", "active", "date_created", "cloud_message_type"
	)
	list_filter = ("active", "cloud_message_type")

	def send_messages(self, request: HttpRequest, queryset: QuerySet, bulk: bool = False) -> None:
		"""
		Provides error handling for DeviceAdmin send_message and send_bulk_message methods.
		"""
		results = []
		errors = []

		if bulk:
			results.append(queryset.send_message("Test bulk notification"))
		else:
			for device in queryset:
				result = device.send_message("Test single notification")
				if result:
					results.append(result)

		for batch in results:
			for response in batch.responses:
				if response.exception:
					errors.append(repr(response.exception))

		if errors:
			self.message_user(
				request, _("Some messages could not be processed: %s") % (", ".join(errors)),
				level=messages.ERROR
			)
		else:
			self.message_user(
				request, _("All messages were sent."),
				level=messages.SUCCESS
			)


class WebPushDeviceAdmin(DeviceAdmin):
	list_display = ("__str__", "browser", "user", "active", "date_created")
	list_filter = ("active", "browser")

	if hasattr(User, "USERNAME_FIELD"):
		search_fields = ("name", "registration_id", "user__%s" % (User.USERNAME_FIELD))
	else:
		search_fields = ("name", "registration_id")


admin.site.register(APNSDevice, DeviceAdmin)
admin.site.register(GCMDevice, GCMDeviceAdmin)
admin.site.register(WNSDevice, DeviceAdmin)
admin.site.register(WebPushDevice, WebPushDeviceAdmin)
