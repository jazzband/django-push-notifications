class NotificationError(Exception):
	pass


# APNS
class APNSError(NotificationError):
	pass


class APNSUnsupportedPriority(APNSError):
	pass


class APNSServerError(APNSError):
	def __init__(self, status):
		super().__init__(status)
		self.status = status


# GCM
class GCMError(NotificationError):
	pass


# Web Push
class WebPushError(NotificationError):
	pass
