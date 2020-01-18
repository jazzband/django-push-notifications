import pytest
from django.db import IntegrityError
from django.test import TestCase
from push_notifications.models import APNSDevice, GCMDevice, WNSDevice, WebPushDevice


class GCMModelTestCase(TestCase):
	def test_throws_error_for_same_gcm_registration_id(self):
		device = GCMDevice.objects.create(
			registration_id="unique_id", cloud_message_type="GCM"
		)
		assert device.id is not None
		with pytest.raises(IntegrityError) as excinfo:
			GCMDevice.objects.create(
				registration_id="unique_id", cloud_message_type="GCM"
			)
		assert "UNIQUE constraint failed" in str(excinfo.value)

	def test_throws_error_for_same_apns_registration_id(self):
		device = APNSDevice.objects.create(
			registration_id="unique_id",
		)
		assert device.id is not None
		with pytest.raises(IntegrityError) as excinfo:
			APNSDevice.objects.create(
				registration_id="unique_id",
			)
		assert "UNIQUE constraint failed" in str(excinfo.value)

	def test_throws_error_for_same_wns_registration_id(self):
		device = WNSDevice.objects.create(
			registration_id="unique_id",
		)
		assert device.id is not None
		with pytest.raises(IntegrityError) as excinfo:
			WNSDevice.objects.create(
				registration_id="unique_id",
			)
		assert "UNIQUE constraint failed" in str(excinfo.value)

	def test_throws_error_for_same_web_registration_id(self):
		device = WebPushDevice.objects.create(
			registration_id="unique_id",
		)
		assert device.id is not None
		with pytest.raises(IntegrityError) as excinfo:
			WebPushDevice.objects.create(
				registration_id="unique_id",
			)
		assert "UNIQUE constraint failed" in str(excinfo.value)
