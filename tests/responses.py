# flake8: noqa
from unittest import mock

from firebase_admin.exceptions import InvalidArgumentError
from firebase_admin.messaging import BatchResponse, SendResponse


FCM_SUCCESS = BatchResponse([SendResponse(resp={"name": "abc"}, exception=None)])
FCM_SUCCESS_MULTIPLE = BatchResponse([
	SendResponse(resp={"name": "abc"}, exception=None),
	SendResponse(resp={"name": "abc2"}, exception=None)
], )


def fcm_invalid_argument(field, description):
	"""An INVALID_ARGUMENT error shaped like FCM's response, naming the invalid field."""
	response = mock.Mock()
	response.json.return_value = {"error": {"details": [{
		"@type": "type.googleapis.com/google.rpc.BadRequest",
		"fieldViolations": [{"field": field, "description": description}],
	}]}}
	return InvalidArgumentError(description, http_response=response)


FCM_INVALID_TOKEN = fcm_invalid_argument(
	"message.token", "The registration token is not a valid FCM registration token"
)
FCM_INVALID_PAYLOAD = fcm_invalid_argument("message.data", "Invalid data payload key: from")
FCM_INVALID_ARGUMENT = InvalidArgumentError("Request contains an invalid argument.")
