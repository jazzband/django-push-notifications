from .apns import apns_fetch_inactive_ids


# This is an APNS-only function right now, but maybe GCM will implement it
# in the future.  But the definition of 'expired' may not be the same.
def get_expired_tokens(application_id):
	return apns_fetch_inactive_ids(application_id)
