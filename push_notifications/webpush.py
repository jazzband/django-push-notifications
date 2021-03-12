from pywebpush import WebPushException, webpush

from .conf import get_manager
from .exceptions import WebPushError


def get_subscription_info(application_id, uri, browser, auth, p256dh):
	url = get_manager().get_wp_post_url(application_id, browser)
	return {
		"endpoint": "{}/{}".format(url, uri),
		"keys": {
			"auth": auth,
			"p256dh": p256dh,
		}
	}


def webpush_send_message(
	uri, message, browser, auth, p256dh, application_id=None, **kwargs
):
	subscription_info = get_subscription_info(application_id, uri, browser, auth, p256dh)

	try:
		response = webpush(
			subscription_info=subscription_info,
			data=message,
			vapid_private_key=get_manager().get_wp_private_key(application_id),
			vapid_claims=get_manager().get_wp_claims(application_id).copy(),
			**kwargs
		)
		results = {"results": [{}]}
		if not response.ok:
			results["results"][0]["error"] = response.content
			results["results"][0]["original_registration_id"] = response.content
		else:
			results["success"] = 1
		return results
	except WebPushException as e:
		raise WebPushError(e.message)
