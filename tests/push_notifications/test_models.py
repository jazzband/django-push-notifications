# coding: utf-8
from django.utils import unittest
from django.core.exceptions import ValidationError
from push_notifications.models import GCMDevice, APNSDevice


class TestModels(unittest.TestCase):
    reg_id_android = 'gJ6YMGzkgSlPEkltUxXD9rGeHiNFvEncsKvu' \
                     'jddDTdf5399FghAv2rr1HH5qUgHTpoNSgSF3' \
                     'CEaHA3P1HbuhJApL0ZHTe_uFYRoK3hfSoH7v' \
                     'M0AIcPmNCHnibEUAoIpPonrt62hmISh3xD9O' \
                     '-S0hQrKJjBbC0RKBrs'

    def setUp(self):
        self.reg_id_ios = self.reg_id_android[:64]
        GCMDevice.objects.filter(registration_id=self.reg_id_android).delete()
        APNSDevice.objects.filter(registration_id=self.reg_id_ios).delete()

        self.android_device = GCMDevice(registration_id=self.reg_id_android)
        self.android_device.save()
        self.ios_device = APNSDevice(registration_id=self.reg_id_ios)
        self.ios_device.save()

    def testGCMDevice(self):
        self.assertEqual(
            GCMDevice.objects.filter(registration_id=self.reg_id_android).count(),
            1
        )

    def testAPNSDevice(self):
        self.assertEqual(
            APNSDevice.objects.filter(registration_id=self.reg_id_ios).count(),
            1
        )

    def testGCMDeviceUniqueness(self):
        self.android_device = GCMDevice(registration_id=self.reg_id_android)
        self.assertRaises(
            ValidationError,
            self.android_device.save
        )