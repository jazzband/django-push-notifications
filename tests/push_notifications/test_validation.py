# coding: utf-8
from django.core.exceptions import ValidationError
from django.utils import unittest
from push_notifications.models import APNSDevice


class TestValidation(unittest.TestCase):
    illegal_id_apple = '8732tqzgedia76tdiua6fugu76grf8a7rtgua76gdf76egtfis7a6egfa76gfia6'

    def test_validation(self):
        self.assertRaises(
            ValidationError,
            APNSDevice.objects.create,
            registration_id=self.illegal_id_apple,
        )