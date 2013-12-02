# coding: utf-8
from _ssl import SSLError
from urllib2 import HTTPError
from django.conf import settings
from django.utils import unittest
from push_notifications.models import APNSDevice, GCMDevice


class TestSending(unittest.TestCase):
    reg_id_android = settings.TEST_ID_ANDROID
    reg_id_ios = settings.TEST_ID_APPLE

    def setUp(self):
        GCMDevice.objects.filter(registration_id=self.reg_id_android).delete()
        APNSDevice.objects.filter(registration_id=self.reg_id_ios).delete()

        self.android_device = GCMDevice(registration_id=self.reg_id_android)
        self.android_device.save()
        self.ios_device = APNSDevice(registration_id=self.reg_id_ios)
        self.ios_device.save()

    def testGCMDeviceSend(self):
        self.assertRaises(
            HTTPError,
            GCMDevice.objects.filter(registration_id=self.reg_id_android).send_message,
            'test_message',
        )

    def testAPNSDeviceSend(self):
        self.assertRaises(
            SSLError,
            APNSDevice.objects.filter(registration_id=self.reg_id_ios).send_message,
            'test_message',
        )
