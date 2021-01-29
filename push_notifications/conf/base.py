from django.core.exceptions import ImproperlyConfigured


class BaseConfig:
	def has_auth_token_creds(self, application_id=None):
		raise NotImplementedError

	def get_apns_certificate(self, application_id=None):
		raise NotImplementedError

	def get_apns_auth_creds(self, application_id=None):
		raise NotImplementedError

	def get_apns_use_sandbox(self, application_id=None):
		raise NotImplementedError

	def get_apns_use_alternative_port(self, application_id=None):
		raise NotImplementedError

	def get_fcm_api_key(self, application_id=None):
		raise NotImplementedError

	def get_gcm_api_key(self, application_id=None):
		raise NotImplementedError

	def get_wns_package_security_id(self, application_id=None):
		raise NotImplementedError

	def get_wns_secret_key(self, application_id=None):
		raise NotImplementedError

	def get_post_url(self, cloud_type, application_id=None):
		raise NotImplementedError

	def get_error_timeout(self, cloud_type, application_id=None):
		raise NotImplementedError

	def get_max_recipients(self, cloud_type, application_id=None):
		raise NotImplementedError

	def get_applications(self):
		"""Returns a collection containing the configured applications."""

		raise NotImplementedError


# This works for both the certificate and the auth key (since that's just
# a certificate).
def check_apns_certificate(ss):
	mode = "start"
	for s in ss.split("\n"):
		if mode == "start":
			if "BEGIN RSA PRIVATE KEY" in s or "BEGIN PRIVATE KEY" in s:
				mode = "key"
		elif mode == "key":
			if "END RSA PRIVATE KEY" in s or "END PRIVATE KEY" in s:
				mode = "end"
				break
			elif s.startswith("Proc-Type") and "ENCRYPTED" in s:
				raise ImproperlyConfigured("Encrypted APNS private keys are not supported")

	if mode != "end":
		raise ImproperlyConfigured("The APNS certificate doesn't contain a private key")
