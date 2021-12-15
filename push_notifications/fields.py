import re
import struct

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import connection, models
from django.utils.translation import gettext_lazy as _


__all__ = ["HexadecimalField", "HexIntegerField"]

UNSIGNED_64BIT_INT_MIN_VALUE = 0
UNSIGNED_64BIT_INT_MAX_VALUE = 2 ** 64 - 1


hex_re = re.compile(r"^(([0-9A-f])|(0x[0-9A-f]))+$")
signed_integer_vendors = [
	"postgresql",
	"sqlite",
]


def _using_signed_storage():
	return connection.vendor in signed_integer_vendors


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
		if value and not isinstance(value, str) \
			and connection.vendor in ("mysql", "sqlite"):
			value = _unsigned_integer_to_hex_string(value)
		return super(forms.CharField, self).prepare_value(value)


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

	validators = [
		MinValueValidator(UNSIGNED_64BIT_INT_MIN_VALUE),
		MaxValueValidator(UNSIGNED_64BIT_INT_MAX_VALUE)
	]

	def db_type(self, connection):
		if "mysql" == connection.vendor:
			return "bigint unsigned"
		elif "sqlite" == connection.vendor:
			return "UNSIGNED BIG INT"
		else:
			return super(HexIntegerField, self).db_type(connection=connection)

	def get_prep_value(self, value):
		""" Return the integer value to be stored from the hex string """
		if value is None or value == "":
			return None
		if isinstance(value, str):
			value = _hex_string_to_unsigned_integer(value)
		if _using_signed_storage():
			value = _unsigned_to_signed_integer(value)
		return value

	def from_db_value(self, value, *args):
		""" Return an unsigned int representation from all db backends """
		if value is None:
			return value
		if _using_signed_storage():
			value = _signed_to_unsigned_integer(value)
		return value

	def to_python(self, value):
		""" Return a str representation of the hexadecimal """
		if isinstance(value, str):
			return value
		if value is None:
			return value
		return _unsigned_integer_to_hex_string(value)

	def formfield(self, **kwargs):
		defaults = {"form_class": HexadecimalField}
		defaults.update(kwargs)
		# yes, that super call is right
		return super(models.IntegerField, self).formfield(**defaults)

	def run_validators(self, value):
		# make sure validation is performed on integer value not string value
		value = _hex_string_to_unsigned_integer(value)
		return super(models.BigIntegerField, self).run_validators(value)
