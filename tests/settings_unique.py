# assert warnings are enabled
import warnings


warnings.simplefilter("ignore", Warning)


DATABASES = {
	"default": {
		"ENGINE": "django.db.backends.sqlite3",
	}
}

INSTALLED_APPS = [
	"django.contrib.admin",
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.sessions",
	"django.contrib.sites",
	"push_notifications",
]

SITE_ID = 1
ROOT_URLCONF = "core.urls"

SECRET_KEY = "foobar"

PUSH_NOTIFICATIONS_SETTINGS = {
	"WP_CLAIMS": {"sub": "mailto: jazzband@example.com"},
	"UNIQUE_REG_ID": True
}
