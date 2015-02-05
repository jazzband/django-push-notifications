from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from .models import APNSDevice, GCMDevice, get_expired_tokens


def _user__username():
	try:
		from django.contrib.auth import get_user_model
	except ImportError:
		# Django <1.5
		return "user__username"
	return "user__%s" % (get_user_model().USERNAME_FIELD)


class DeviceAdmin(admin.ModelAdmin):
	list_display = ("__unicode__", "device_id", "user", "active", "date_created")
	search_fields = ("name", "device_id", _user__username())
	list_filter = ("active", )
	actions = ("send_message", "send_bulk_message", "prune_devices", "enable", "disable")

	def send_message(self, request, queryset):
		ret = []
		errors = []
		r = ""
		for device in queryset:
			try:
				r = device.send_message("Test single notification")
			except Exception as e:
				errors.append(str(e))
			if r:
				ret.append(r)
		if errors:
			self.message_user(request, _("Some messages could not be processed: %r" % ("\n".join(errors))))
		if ret:
			self.message_user(request, _("All messages were sent: %s" % ("\n".join(ret))))
	send_message.short_description = _("Send test message")

	def send_bulk_message(self, request, queryset):
		r = queryset.send_message("Test bulk notification")
		self.message_user(request, _("All messages were sent: %s" % (r)))
	send_bulk_message.short_description = _("Send test message in bulk")

	def enable(self, request, queryset):
		queryset.update(active=True)
	enable.short_description = _("Enable selected devices")

	def disable(self, request, queryset):
		queryset.update(active=False)
	disable.short_description = _("Disable selected devices")

	def prune_devices(self, request, queryset):
		# Note that when get_expired_tokens() is called, Apple's
		# feedback service resets, so, calling it again won't return
		# the device again (unless a message is sent to it again).  So,
		# if the user doesn't select all the devices for pruning, we
		# could very easily leave an expired device as active.  Maybe
		#  this is just a bad API.
		expired = get_expired_tokens()
		devices = queryset.filter(registration_id__in=expired)
		for d in devices:
			d.active = False
			d.save()


admin.site.register(APNSDevice, DeviceAdmin)
admin.site.register(GCMDevice, DeviceAdmin)
