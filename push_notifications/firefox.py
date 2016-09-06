import requests

from .settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS


def firefox_send_message(registration_id):
	url = SETTINGS['FIREFOX_POST_URL'] + registration_id
	response = requests.post(url, headers=SETTINGS['FIREFOX_HEADERS'])
	if response.ok:
		return 'ok'
	return 'no-ok'