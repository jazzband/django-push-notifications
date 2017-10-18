from . import NotificationError
from .conf import get_manager


class WebPushError(NotificationError):
	pass


def get_subscription_info(application_id, uri, browser, auth, p256dh):
	url = get_manager().get_browser_post_url(application_id, browser)
	return {
		"endpoint": "%s/%s" % (url, uri),
		"keys": {
			"auth": auth,
			"p256dh": p256dh
		}
	}


def webpush_send_message(uri, message, browser, auth, p256dh, application_id=None, **kwargs):
	try:
		from pywebpush import webpush
		from pywebpush import WebPushException
	except ImportError:
		raise WebPushError("Please install pywebpush package: pip install pywebpush")
	try:
		response = webpush(
			subscription_info=get_subscription_info(application_id, uri, browser, auth, p256dh),
			data=message,
			vapid_private_key=get_manager().get_browser_private_key(application_id),
			vapid_claims=get_manager().get_browser_claims(application_id),
			**kwargs)
		results = {"results": [{}]}
		if not response.ok:
			results["results"][0]['error'] = response.content
			results["results"][0]['original_registration_id'] = response.content
		else:
			results["success"] = 1
		return results
	except WebPushException as e:
		raise WebPushError(e.message)
