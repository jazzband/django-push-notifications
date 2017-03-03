from apns2 import errors as apns2_errors


def reason_for_exception_class(exception_class):
	return {
		apns2_errors.PayloadEmpty: "PayloadEmpty",
		apns2_errors.PayloadTooLarge: "PayloadTooLarge",
		apns2_errors.BadTopic: "BadTopic",
		apns2_errors.TopicDisallowed: "TopicDisallowed",
		apns2_errors.BadMessageId: "BadMessageId",
		apns2_errors.BadExpirationDate: "BadExpirationDate",
		apns2_errors.BadPriority: "BadPriority",
		apns2_errors.MissingDeviceToken: "MissingDeviceToken",
		apns2_errors.BadDeviceToken: "BadDeviceToken",
		apns2_errors.DeviceTokenNotForTopic: "DeviceTokenNotForTopic",
		apns2_errors.Unregistered: "Unregistered",
		apns2_errors.DuplicateHeaders: "DuplicateHeaders",
		apns2_errors.BadCertificateEnvironment: "BadCertificateEnvironment",
		apns2_errors.BadCertificate: "BadCertificate",
		apns2_errors.Forbidden: "Forbidden",
		apns2_errors.BadPath: "BadPath",
		apns2_errors.MethodNotAllowed: "MethodNotAllowed",
		apns2_errors.TooManyRequests: "TooManyRequests",
		apns2_errors.IdleTimeout: "IdleTimeout",
		apns2_errors.Shutdown: "Shutdown",
		apns2_errors.InternalServerError: "InternalServerError",
		apns2_errors.ServiceUnavailable: "ServiceUnavailable",
		apns2_errors.MissingTopic: "MissingTopic"
	}[exception_class]
