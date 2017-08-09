import re
import struct
from django import forms
from django.core.validators import RegexValidator
from django.db import connection, models
from django.utils import six
from django.utils.translation import ugettext_lazy as _


__all__ = ["HexadecimalField", "HexIntegerField"]

UNSIGNED_64BIT_INT_MIN_VALUE = 0
UNSIGNED_64BIT_INT_MAX_VALUE = 2 ** 64 - 1


hex_re = re.compile(r"^(([0-9A-f])|(0x[0-9A-f]))+$")
signed_integer_engines = [
	"django.db.backends.postgresql",
	"django.db.backends.postgresql_psycopg2",
	"django.contrib.gis.db.backends.postgis",
	"django.db.backends.sqlite3"
]


def _using_signed_storage():
	return connection.settings_dict["ENGINE"] in signed_integer_engines


def _signed_to_unsigned_integer(value):
	return struct.unpack("Q", struct.pack("q", value))[0]


def _unsigned_to_signed_integer(value):
	return struct.unpack("q", struct.pack("Q", value))[0]


def _hex_string_to_unsigned_integer(value):
	return int(value, 16)


def _unsigned_integer_to_hex_string(value):
	return hex(value).rstrip("L")


class HexadecimalField(forms.CharField):
	"""
	A form field that accepts only hexadecimal numbers
	"""
	def __init__(self, *args, **kwargs):
		self.default_validators = [
			RegexValidator(hex_re, _("Enter a valid hexadecimal number"), "invalid")
		]
		super(HexadecimalField, self).__init__(*args, **kwargs)

	def prepare_value(self, value):
		# converts bigint from db to hex before it is displayed in admin
		if value and not isinstance(value, six.string_types) \
			and connection.vendor in ("mysql", "sqlite"):
			value = _unsigned_integer_to_hex_string(value)
		return super(forms.CharField, self).prepare_value(value)


# https://docs.djangoproject.com/en/1.11/topics/migrations/#considerations-when-removing-model-fields
class HexIntegerField(models.BigIntegerField):
	"""
	This field stores a hexadecimal *string* of up to 64 bits as an unsigned integer
	on *all* backends including postgres.

	Reasoning: Postgres only supports signed bigints. Since we don't care about
	signedness, we store it as signed, and cast it to unsigned when we deal with
	the actual value (with struct)

	On sqlite and mysql, native unsigned bigint types are used. In all cases, the
	value we deal with in python is always in hex.
	"""

	system_check_removed_details = {
		"msg": (
			"HexIntegerField has been removed except for support in "
			"historical migrations."
		),
		"hint": "Use UUIDField instead.",
		"id": "fields.E001",
	}
