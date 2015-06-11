GCM_PLAIN_RESPONSE = 'id=1:08'
GCM_JSON_RESPONSE = '{"multicast_id":108,"success":1,"failure":0,"canonical_ids":0,"results":[{"message_id":"1:08"}]}'
GCM_MULTIPLE_JSON_RESPONSE = '{"multicast_id":108,"success":2,"failure":0,"canonical_ids":0,"results":[{"message_id":"1:08"}, {"message_id": "1:09"}]}'
GCM_PLAIN_RESPONSE_ERROR = ['Error=NotRegistered', 'Error=InvalidRegistration']
GCM_PLAIN_RESPONSE_ERROR_B = 'Error=MismatchSenderId'
GCM_JSON_RESPONSE_ERROR = '{"failure": 3, "canonical_ids": 0, "cast_id": 6358665107659088804, "results": [{"error": "NotRegistered"}, {"message_id": "0:1433830664381654%3449593ff9fd7ecd"}, {"error": "InvalidRegistration"}]}'