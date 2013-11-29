# coding: utf-8
from django.conf import settings
from django.utils import unittest
from django.core.exceptions import ValidationError
from push_notifications.models import GCMDevice, APNSDevice


class TestModels(unittest.TestCase):
    reg_id_android = settings.TEST_ID_ANDROID
    reg_id_ios = settings.TEST_ID_APPLE

    def setUp(self):
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