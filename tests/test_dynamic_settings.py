import json
import mock
from django.test import TestCase
from django.utils import timezone
from push_notifications import dynamic
from django.conf import settings

from django.core.exceptions import ImproperlyConfigured

from push_notifications.models import ApplicationModel

class DynamicSettingsTestCase(TestCase):
    def test_base_settings(self):
        settings.PUSH_NOTIFICATIONS_SETTINGS['TEST'] = 'test'
        assert dynamic._get_application_settings('qwerty','TEST','Test Exception') == 'test'
        settings.PUSH_NOTIFICATIONS_SETTINGS['TESTS'] = {
            'qwerty':'uiop'
        }
        assert dynamic._get_application_settings('qwerty','TEST','Test Exception') == 'uiop'
        assert dynamic._get_application_settings('uiop','TEST','Test Exception') == 'test'
        try:
            dynamic._get_application_settings('qwerty','NOTPRESENT','Test Exception')
            assert False
        except Exception as ex:
            assert type(ex) == ImproperlyConfigured
            assert ex.args and ex.args[0] == 'Test Exception'

    def test_default_if_none(self):
        settings.PUSH_NOTIFICATIONS_SETTINGS['TEST'] = 'test'
        settings.PUSH_NOTIFICATIONS_SETTINGS['TESTS'] = {
            'qwerty':'uiop',
            'qwerty2':None
        }
        assert dynamic._get_application_settings('qwerty','TEST','Test Exception') == 'uiop'
        assert dynamic._get_application_settings('qwerty2','TEST','Test Exception') == 'test'

    def test_database_settings(self):
        settings.PUSH_NOTIFICATIONS_SETTINGS['TEST'] = 'test'
        settings.PUSH_NOTIFICATIONS_SETTINGS['TESTS_MODEL'] = {
            'model':'push_notifications.ApplicationModel',
            'key':'application_id',
            'value':'gcm_api_key',
        }
        ApplicationModel.objects.create(application_id='qwerty2',gcm_api_key='uiop2')
        assert dynamic._get_application_settings('qwerty2','TEST','Test Exception') == 'uiop2'
        assert dynamic._get_application_settings('uiop2','TEST','Test Exception') == 'test'
        try:
            dynamic._get_application_settings('qwerty','NOTPRESENT','Test Exception')
            assert False
        except Exception as ex:
            assert type(ex) == ImproperlyConfigured
            assert ex.args and ex.args[0] == 'Test Exception'

    def test_push_settings(self):
        try:
            r = dynamic.get_gcm_api_key()
            assert False
        except Exception as ex:
            assert type(ex) == ImproperlyConfigured
        settings.PUSH_NOTIFICATIONS_SETTINGS['GCM_API_KEY'] = 'testkey'
        settings.PUSH_NOTIFICATIONS_SETTINGS['APNS_CERTIFICATE'] = 'testcert'
        assert dynamic.get_gcm_api_key() == 'testkey'
        assert dynamic.get_apns_certificate() == 'testcert'

        settings.PUSH_NOTIFICATIONS_SETTINGS['GCM_API_KEYS'] = {
            'qwerty':'uiopkey'
        }
        settings.PUSH_NOTIFICATIONS_SETTINGS['APNS_CERTIFICATES'] = {
            'qwerty':'uiopcert'
        }
        assert dynamic.get_gcm_api_key() == 'testkey'
        assert dynamic.get_apns_certificate() == 'testcert'
        assert dynamic.get_gcm_api_key('uiop') == 'testkey'
        assert dynamic.get_apns_certificate('uiop') == 'testcert'
        assert dynamic.get_gcm_api_key('qwerty') == 'uiopkey'
        assert dynamic.get_apns_certificate('qwerty') == 'uiopcert'
