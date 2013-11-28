# coding: utf-8
from push_notifications.models import GCMDevice, APNSDevice
from django.utils.unittest.case import TestCase


class TestModels(TestCase):
    reg_id_android = 'gJ6YMGzkgSlPEkltUxXD9rGeHiNFvEncsKvu' \
                     'jddDTdf5399FghAv2rr1HH5qUgHTpoNSgSF3' \
                     'CEaHA3P1HbuhJApL0ZHTe_uFYRoK3hfSoH7v' \
                     'M0AIcPmNCHnibEUAoIpPonrt62hmISh3xD9O' \
                     '-S0hQrKJjBbC0RKBrs'

    def setUp(self):
        self.reg_id_ios = self.reg_id_android[:64]
        self.android_device = GCMDevice(registration_id=self.reg_id_android)
        self.android_device.save()
        self.ios_device = APNSDevice(registration_id=self.reg_id_ios)
        self.ios_device.save()

    def testIDs(self):
        self.assertEqual(
            GCMDevice.objects.filter(registration_id=self.reg_id_android).count(),
            1
        )
        self.assertEqual(
            APNSDevice.objects.filter(registration_id=self.reg_id_ios).count(),
            1
        )
