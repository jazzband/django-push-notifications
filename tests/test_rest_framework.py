from django.test import TestCase
from push_notifications.api.rest_framework import APNSDeviceSerializer, GCMDeviceSerializer
from rest_framework.serializers import ValidationError
from tests.mock_responses import GCM_DRF_INVALID_HEX_ERROR, GCM_DRF_OUT_OF_RANGE_ERROR


class APNSDeviceSerializerTestCase(TestCase):
	def test_validation(self):
		# valid data - 32 bytes upper case
		serializer = APNSDeviceSerializer(data={
			"registration_id": "AEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAE",
			"name": "Apple iPhone 6+",
			"device_id": "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
		})
		self.assertTrue(serializer.is_valid())

		# valid data - 32 bytes lower case
		serializer = APNSDeviceSerializer(data={
			"registration_id": "aeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeae",
			"name": "Apple iPhone 6+",
			"device_id": "ffffffffffffffffffffffffffffffff",
		})
		self.assertTrue(serializer.is_valid())

		# valid data - 100 bytes upper case
		serializer = APNSDeviceSerializer(data={
			"registration_id": "AEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAEAE",
			"name": "Apple iPhone 6+",
			"device_id": "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
		})
		self.assertTrue(serializer.is_valid())

		# valid data - 100 bytes lower case
		serializer = APNSDeviceSerializer(data={
			"registration_id": "aeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeae",
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

	def test_registration_id_unique(self):
		"""Validate that a duplicate registration id raises a validation error."""

		# add a device
		serializer = GCMDeviceSerializer(data={
			"registration_id": "foobar",
			"name": "Galaxy Note 3",
			"device_id": "0x1031af3b",
		})
		serializer.is_valid(raise_exception=True)
		obj = serializer.save()

		# ensure updating the same object works
		serializer = GCMDeviceSerializer(obj, data={
			"registration_id": "foobar",
			"name": "Galaxy Note 5",
			"device_id": "0x1031af3b",
		})
		serializer.is_valid(raise_exception=True)
		obj = serializer.save()

		# try to add a new device with the same token
		serializer = GCMDeviceSerializer(data={
			"registration_id": "foobar",
			"name": "Galaxy Note 3",
			"device_id": "0xdeadbeaf",
		})

		with self.assertRaises(ValidationError) as ex:
			serializer.is_valid(raise_exception=True)
		self.assertEqual({'registration_id': [u'This field must be unique.']}, ex.exception.detail)

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
			"device_id": "10000000000000000", # 2**64
		})
		self.assertFalse(serializer.is_valid())
		self.assertEqual(serializer.errors, GCM_DRF_OUT_OF_RANGE_ERROR)

	def test_device_id_validation_value_between_signed_unsigned_64b_int_maximums(self):
		"""
		2**63 < 0xe87a4e72d634997c < 2**64
		"""
		serializer = GCMDeviceSerializer(data={
			"registration_id": "foobar",
			"name": "Nexus 5",
			"device_id": "e87a4e72d634997c",
		})
		self.assertTrue(serializer.is_valid())
