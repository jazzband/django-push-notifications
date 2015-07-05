from django.core import checks
from django.utils.translation import ugettext as _

# Minimum Django version required for Django Push Notifications to run.
DJANGO_MINIMUM_REQUIRED_VERSION = (1, 8, 0)


def _version_to_string(version, significance=None):
	if significance is not None:
		version = version[significance:]
	return ".".join(str(n) for n in version)


@checks.register()
def check_library_versions(app_configs=None, **kwargs):
	from django import VERSION as django_version

	errors = []

	if django_version < DJANGO_MINIMUM_REQUIRED_VERSION:
		errors.append(checks.Critical(
			_("Your version of Django is too old."),
			hint=_("Try pip install --upgrade 'Django==%s'", _version_to_string(DJANGO_MINIMUM_REQUIRED_VERSION)),
			id="django_push_notifications.C001",
		))

	return errors


@checks.register()
def check_apns_settings(app_configs=None, **kwargs):
	from .settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS
	dpn_settings = SETTINGS.copy()

	errors = []

	if "APNS_CERTIFICATE" in dpn_settings:
		cert = dpn_settings.pop("APNS_CERTIFICATE", None)
		ca_cert = dpn_settings.pop("APNS_CA_CERTIFICATES", None)

		dpn_settings["APNS_APP_CERTIFICATES"] = {
			"APP": {
				"APNS_CERTIFICATE": cert,
				"APNS_CA_CERTIFICATES": ca_cert
			}
		}

		errors.append(checks.Warning(
			_("Use the new APNS Certificates format."),
			hint="""
			Here is how to format your current settings:
			{s}
			""".format(s=dpn_settings),
			id="django_push_notifications.W001"
		))

	if "APNS_APP_CERTIFICATES" in SETTINGS:
		apns_app_settings = SETTINGS.get("APNS_APP_CERTIFICATES", None)
		if not len(apns_app_settings):
			errors.append(checks.Error(
				_('You need to set at least one app in ["APNS_APP_CERTIFICATES"] to send messages through APNS.'),
				id="django_push_notifications.E001"
			))

		for app_name, certificate_settings in apns_app_settings.items():
			cert = certificate_settings.get("APNS_CERTIFICATE", None)
			if not cert:
				errors.append(checks.Error(
					_("Missing certificate for APP {name}").format(name=app_name),
					id="django_push_notifications.E002",
					hint=_('Set PUSH_NOTIFICATIONS_SETTINGS["APNS_APP_CERTIFICATES"]["{name}"]["APNS_CERTIFICATE"]')
				))
			else:
				# ensure the certificate is readable
				try:
					with open(cert, "r") as f:
						f.read()
				except Exception as ex:
					errors.append(checks.Error(
						_("The APNS certificate file for {app} at {path} is not readable: {ex}").format(
							app=app_name,
							path=cert,
							ex=ex
						),
						id="django_push_notifications.E003",
					))

	return errors
