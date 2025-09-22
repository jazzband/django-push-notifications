import warnings

from pywebpush import WebPushException, webpush
from typing import Dict, Any
from .conf import get_manager
from .exceptions import WebPushError


def get_subscription_info(
	application_id: str, uri: str, browser: str, auth: str, p256dh: str
) -> Dict[str, Any]:
	if uri.startswith("https://"):
		endpoint = uri
	else:
		manager = get_manager()
		if hasattr(manager, "get_wp_post_url"):
			url = manager.get_wp_post_url(application_id, browser)
		else:
			raise AttributeError("Manager does not support get_wp_post_url method")
		endpoint = "{}/{}".format(url, uri)
		warnings.warn(
			"registration_id should be the full endpoint returned from pushManager.subscribe",
			DeprecationWarning,
			stacklevel=2,
		)
	return {
		"endpoint": endpoint,
		"keys": {
			"auth": auth,
			"p256dh": p256dh,
		},
	}


def webpush_send_message(device: Any, message: str, **kwargs: Any) -> Dict[str, Any]:
	subscription_info = get_subscription_info(
		device.application_id,
		device.registration_id,
		device.browser,
		device.auth,
		device.p256dh,
	)
	try:
		results = {"results": [{"original_registration_id": device.registration_id}]}
		manager = get_manager()

		vapid_private_key = None
		if hasattr(manager, "get_wp_private_key"):
			vapid_private_key = manager.get_wp_private_key(device.application_id)

		vapid_claims = None
		if hasattr(manager, "get_wp_claims"):
			vapid_claims = manager.get_wp_claims(device.application_id).copy()

		timeout = None
		if hasattr(manager, "get_wp_error_timeout"):
			timeout = manager.get_wp_error_timeout(device.application_id)

		response = webpush(
			subscription_info=subscription_info,
			data=message,
			vapid_private_key=vapid_private_key,
			vapid_claims=vapid_claims,
			timeout=timeout,
			**kwargs,
		)
		if response.ok:
			results["success"] = 1
		else:
			results["failure"] = 1
			results["results"][0]["error"] = response.content
		return results
	except WebPushException as e:
		if e.response is not None and e.response.status_code in [404, 410]:
			results["failure"] = 1
			results["results"][0]["error"] = e.message
			device.active = False
			device.save()
			return results
		raise WebPushError(e.message)
