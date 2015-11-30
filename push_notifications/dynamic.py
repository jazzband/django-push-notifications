from django.core.exceptions import ImproperlyConfigured
from . import NotificationError
from .settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS
from .modeldict import FieldPairDict

def _get_application_settings(application_id,settings_key,error_message):
    if not application_id: # old behaviour
        value = SETTINGS.get(settings_key,None)
        if not value:
            raise ImproperlyConfigured(error_message)
        return value
    # new behaviour, settings dict
    values = SETTINGS.get(settings_key+"S",{})

    if values.has_key(application_id):
        value = values.get(application_id)
        if value is not None:
            return value

    # new behaviour, getting from the model
    values_model = SETTINGS.get(settings_key+"S_MODEL",None)
    if values_model:
        model = values_model.get('model',None)
        key = values_model.get('key',None)
        value = values_model.get('value',None)
        if model and key and value:
            values = FieldPairDict(model,key,value)

    if values.has_key(application_id):
        value = values.get(application_id)
        if value is not None:
            return value

    value = SETTINGS.get(settings_key,None)
    if not value:
        raise ImproperlyConfigured(error_message)
    return value

def get_gcm_api_key(application_id=None):
    return _get_application_settings(application_id,"GCM_API_KEY",'You need to setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages')

def get_apns_certificate(application_id=None):
    r = _get_application_settings(application_id,"APNS_CERTIFICATE",'You need to setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages')
    if not isinstance(r,basestring):
        # probably the (Django) file, and file path should be got
        if hasattr(r,'path'):
            return r.path
        elif hasattr(r,'has_key') and r.has_key('path'):
            return r['path']
        else:
            raise ImproperlyConfigured("The APNS certificate settings value should be a string, or should have a 'path' attribute or key")
    return r
