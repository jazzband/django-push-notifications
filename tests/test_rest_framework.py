from django.test import TestCase
from push_notifications.api.rest_framework import APNSDeviceSerializer


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
