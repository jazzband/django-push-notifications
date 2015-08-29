from django.test import TestCase
from push_notifications.api.rest_framework import APNSDeviceSerializer, GCMDeviceSerializer
from tests.mock_responses import GCM_DRF_INVALID_HEX_ERROR, GCM_DRF_OUT_OF_RANGE_ERROR


class APNSDeviceSerializerTestCase(TestCase):
	def test_validation(self):
		# valid data - upper case
		serializer = APNSDeviceSerializer(data={
			"registration_id": "AEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAE",
			"name": "Apple iPhone 6+",
			"device_id": "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
		})
		self.assertTrue(serializer.is_valid())

		# valid data - lower case
		serializer = APNSDeviceSerializer(data={
			"registration_id": "aeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeae",
			"name": "Apple iPhone 6+",
			"device_id": "ffffffffffffffffffffffffffffffff",
		})
		self.assertTrue(serializer.is_valid())

		# invalid data - device_id, registration_id
		serializer = APNSDeviceSerializer(data={
			"registration_id": "invalid device token contains no hex",
			"name": "Apple iPhone 6+",
			"device_id": "ffffffffffffffffffffffffffffake",
		})
		self.assertFalse(serializer.is_valid())
		self.assertEqual(serializer.errors["device_id"][0], '"ffffffffffffffffffffffffffffake" is not a valid UUID.')
		self.assertEqual(serializer.errors["registration_id"][0], "Registration ID (device token) is invalid")


class GCMDeviceSerializerTestCase(TestCase):
	def test_device_id_validation_pass(self):
		serializer = GCMDeviceSerializer(data={
			"registration_id": "foobar",
			"name": "Galaxy Note 3",
			"device_id": "0x1031af3b",
		})
		self.assertTrue(serializer.is_valid())

	def test_device_id_validation_fail_bad_hex(self):
		serializer = GCMDeviceSerializer(data={
			"registration_id": "foobar",
			"name": "Galaxy Note 3",
			"device_id": "0x10r",
		})
		self.assertFalse(serializer.is_valid())
		self.assertEqual(serializer.errors, GCM_DRF_INVALID_HEX_ERROR)

	def test_device_id_validation_fail_out_of_range(self):
		serializer = GCMDeviceSerializer(data={
			"registration_id": "foobar",
			"name": "Galaxy Note 3",
			"device_id": "a54eb38370070a1b",
		})
		self.assertFalse(serializer.is_valid())
		self.assertEqual(serializer.errors, GCM_DRF_OUT_OF_RANGE_ERROR)
