# flake8: noqa


GCM_JSON = '{"cast_id":108,"success":1,"failure":0,"canonical_ids":0,"results":[{"message_id":"1:08"}]}'
GCM_JSON_ERROR_NOTREGISTERED = (
	'{"failure": 1, "canonical_ids": 0, "cast_id": 6358665107659088804, "results":'
	' [{"error": "NotRegistered"}]}'
)
GCM_JSON_ERROR_INVALIDREGISTRATION = (
	'{"failure": 1, "canonical_ids": 0, "cast_id": 6358665107659088804, "results":'
	' [{"error": "InvalidRegistration"}]}'
)
GCM_JSON_ERROR_MISMATCHSENDERID = (
	'{"success":0, "failure": 1, "canonical_ids": 0, "results":'
	' [{"error": "MismatchSenderId"}]}'
)
GCM_JSON_CANONICAL_ID = (
	'{"failure":0,"canonical_ids":1,"success":1,"cast_id":7173139966327257000,"results":'
	'[{"registration_id":"NEW_REGISTRATION_ID","message_id":"0:1440068396670935%6868637df9fd7ecd"}]}'
)
GCM_JSON_CANONICAL_ID_SAME_DEVICE = (
	'{"failure":0,"canonical_ids":1,"success":1,"cast_id":7173139966327257000,"results":'
	'[{"registration_id":"bar","message_id":"0:1440068396670935%6868637df9fd7ecd"}]}'
)

GCM_JSON_MULTIPLE = (
	'{"multicast_id":108,"success":2,"failure":0,"canonical_ids":0,"results":'
	'[{"message_id":"1:08"}, {"message_id": "1:09"}]}'
)
GCM_JSON_MULTIPLE_ERROR = (
	'{"success":1, "failure": 2, "canonical_ids": 0, "cast_id": 6358665107659088804, "results":'
	' [{"error": "NotRegistered"}, {"message_id": "0:1433830664381654%3449593ff9fd7ecd"}, '
	'{"error": "InvalidRegistration"}]}'
)
GCM_JSON_MULTIPLE_ERROR_B = (
	'{"success":1, "failure": 2, "canonical_ids": 0, "cast_id": 6358665107659088804, '
	'"results": [{"error": "MismatchSenderId"}, {"message_id": '
	'"0:1433830664381654%3449593ff9fd7ecd"}, {"error": "InvalidRegistration"}]}'
)
GCM_JSON_MULTIPLE_CANONICAL_ID = (
	'{"failure":0,"canonical_ids":1,"success":2,"multicast_id":7173139966327257000,"results":'
	'[{"registration_id":"NEW_REGISTRATION_ID","message_id":"0:1440068396670935%6868637df9fd7ecd"},'
	'{"message_id":"0:1440068396670937%6868637df9fd7ecd"}]}'
)
GCM_JSON_MULTIPLE_CANONICAL_ID_SAME_DEVICE = (
	'{"failure":0,"canonical_ids":1,"success":2,"multicast_id":7173139966327257000,'
	'"results":[{"registration_id":"bar","message_id":"0:1440068396670935%6868637df9fd7ecd"}'
	',{"message_id":"0:1440068396670937%6868637df9fd7ecd"}]}'
)
