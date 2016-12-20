import re
import struct
from django import forms
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.core.validators import RegexValidator
from django.db import models, connection
from django.utils import six
from django.utils.translation import ugettext_lazy as _

UNSIGNED_64BIT_INT_MIN_VALUE = 0
UNSIGNED_64BIT_INT_MAX_VALUE = 2 ** 64 - 1

__all__ = ["HexadecimalField", "HexIntegerField"]


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
