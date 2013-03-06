from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from uuidfield import UUIDField


class Device(models.Model):
	name = models.CharField(max_length=255, verbose_name=_("Name"), blank=True, null=True)
	active = models.BooleanField(verbose_name=_("Is active"), default=True, help_text=_("Inactive devices will not be sent notifications"))
	user = models.ForeignKey("auth.User", blank=True, null=True)

	class Meta:
		abstract = True

	def __unicode__(self):
		return self.name or str(self.device_id or "") or "%s for %s" % (self.__class__.__name__, self.user or "unknown user")



class GCMDeviceManager(models.Manager):
	def get_query_set(self):
		return GCMDeviceQuerySet(self.model)


class GCMDeviceQuerySet(models.query.QuerySet):
	def send_message(self, message):
		from .gcm import gcm_send_bulk_message
		return gcm_send_bulk_message(registration_ids=list(self.values_list("registration_id", flat=True)), data={"msg": message}, collapse_key="message")


class GCMDevice(Device):
	# device_id cannot be a reliable primary key as fragmentation between different devices
	# can make it turn out to be null and such:
	# http://android-developers.blogspot.co.uk/2011/03/identifying-app-installations.html
	device_id = UUIDField(verbose_name=_("Device ID"), blank=True, null=True, help_text="ANDROID_ID / TelephonyManager.getDeviceId()")
	registration_id = models.TextField(verbose_name=_("Registration ID"))

	objects = GCMDeviceManager()

	class Meta:
		verbose_name = _("GCM device")

	def send_message(self, message):
		from .gcm import gcm_send_message
		return gcm_send_message(registration_id=self.registration_id, data={"msg": message}, collapse_key="message")


class APNSDevice(Device):
	device_id = UUIDField(verbose_name=_("Device ID"), blank=True, null=True, help_text="UDID / UIDevice.identifierForVendor()")
	registration_id = models.CharField(max_length=64)

	class Meta:
		verbose_name = _("APNS device")
