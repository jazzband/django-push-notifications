GCM_PLAIN_RESPONSE = 'id=1:08'
GCM_JSON_RESPONSE = '{"multicast_id":108,"success":1,"failure":0,"canonical_ids":0,"results":[{"message_id":"1:08"}]}'
GCM_MULTIPLE_JSON_RESPONSE = ('{"multicast_id":108,"success":2,"failure":0,"canonical_ids":0,"results":'
							  '[{"message_id":"1:08"}, {"message_id": "1:09"}]}')
GCM_PLAIN_RESPONSE_ERROR = ['Error=NotRegistered', 'Error=InvalidRegistration']
GCM_PLAIN_RESPONSE_ERROR_B = 'Error=MismatchSenderId'
GCM_PLAIN_CANONICAL_ID_RESPONSE = "id=1:2342\nregistration_id=NEW_REGISTRATION_ID"
GCM_JSON_RESPONSE_ERROR = ('{"success":1, "failure": 2, "canonical_ids": 0, "cast_id": 6358665107659088804, "results":'
						   ' [{"error": "NotRegistered"}, {"message_id": "0:1433830664381654%3449593ff9fd7ecd"}, '
						   '{"error": "InvalidRegistration"}]}')
GCM_JSON_RESPONSE_ERROR_B = ('{"success":1, "failure": 2, "canonical_ids": 0, "cast_id": 6358665107659088804, '
							 '"results": [{"error": "MismatchSenderId"}, {"message_id": '
							 '"0:1433830664381654%3449593ff9fd7ecd"}, {"error": "InvalidRegistration"}]}')
GCM_DRF_INVALID_HEX_ERROR = {'device_id': [u"Device ID is not a valid hex number"]}
GCM_DRF_OUT_OF_RANGE_ERROR = {'device_id': [u"Device ID is out of range"]}
GCM_JSON_CANONICAL_ID_RESPONSE = '{"failure":0,"canonical_ids":1,"success":2,"multicast_id":7173139966327257000,"results":[{"registration_id":"NEW_REGISTRATION_ID","message_id":"0:1440068396670935%6868637df9fd7ecd"},{"message_id":"0:1440068396670937%6868637df9fd7ecd"}]}'
GCM_JSON_CANONICAL_ID_SAME_DEVICE_RESPONSE = '{"failure":0,"canonical_ids":1,"success":2,"multicast_id":7173139966327257000,"results":[{"registration_id":"bar","message_id":"0:1440068396670935%6868637df9fd7ecd"},{"message_id":"0:1440068396670937%6868637df9fd7ecd"}]}'
