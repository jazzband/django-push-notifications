# flake8: noqa
from firebase_admin.messaging import BatchResponse, SendResponse


FCM_SUCCESS = BatchResponse([SendResponse(resp={"name": "abc"}, exception=None)])
FCM_SUCCESS_MULTIPLE = BatchResponse([
	SendResponse(resp={"name": "abc"}, exception=None),
	SendResponse(resp={"name": "abc2"}, exception=None)
], )
