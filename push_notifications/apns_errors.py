from apns2 import errors as apns2_errors


def reason_for_exception_class(exception_class):
	errors = {
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
		apns2_errors.MissingTopic: "MissingTopic",
		apns2_errors.BadCollapseId: "BadCollapseId",
		apns2_errors.ConnectionFailed: "ConnectionFailed",
		apns2_errors.ExpiredProviderToken: "ExpiredProviderToken",
		apns2_errors.InternalException: "InternalException",
		apns2_errors.InvalidProviderToken: "InvalidProviderToken",
		apns2_errors.MissingProviderToken: "MissingProviderToken",
		apns2_errors.TooManyProviderTokenUpdates: "TooManyProviderTokenUpdates"
	}
	if exception_class in errors:
		return errors[exception_class]
	return "Unknown APNS error"
