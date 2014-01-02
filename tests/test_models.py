from django.test import TestCase
from push_notifications.models import GCMDevice, APNSDevice


class ModelTestCase(TestCase):
	def test_can_save_gcm_device(self):
		device = GCMDevice.objects.create(
			registration_id="a valid registration id",
		)
		assert device.id is not None

	def test_can_create_save_device(self):
		device = APNSDevice.objects.create(
			registration_id="a valid registration id",
		)
		assert device.id is not None
