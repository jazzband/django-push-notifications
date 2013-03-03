from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from .models import GCMDevice


class GCMDeviceAdmin(admin.ModelAdmin):
	list_display = ("__unicode__", "device_id", "user", "active")
	search_fields = ("name", "device_id", "user__username")
	list_filter = ("active", )
	actions = ("send_message", "send_bulk_message")

	def send_message(self, request, queryset):
		ret = []
		errors = []
		r = ""
		for device in queryset:
			try:
				r = device.send_message("Test single notification")
			except Exception, e:
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


admin.site.register(GCMDevice, GCMDeviceAdmin)
