import re
import struct
from django import forms
from django.core.validators import RegexValidator
from django.db import models, connection
from django.utils.translation import ugettext_lazy as _

try:
	from django.utils import six
except ImportError:
	import six


__all__ = ["HexadecimalField", "HexIntegerField"]

hex_re = re.compile(r"^0x[0-9a-fA-F]+$")
postgres_engines = [
	"django.db.backends.postgresql_psycopg2",
	"django.contrib.gis.db.backends.postgis",
]


class HexadecimalField(forms.CharField):
	"""
	A form field that accepts only hexadecimal numbers
	"""
	def __init__(self, *args, **kwargs):
		self.default_validators = [RegexValidator(hex_re, _("Enter a valid hexadecimal number"), "invalid")]
		super(HexadecimalField, self).__init__(*args, **kwargs)


class HexIntegerField(six.with_metaclass(models.SubfieldBase, models.BigIntegerField)):
	"""
	This field stores a hexadecimal *string* of up to 64 bits as an unsigned integer
	on *all* backends including postgres.

	Reasoning: Postgres only supports signed bigints. Since we don't care about
	signedness, we store it as signed, and cast it to unsigned when we deal with
	the actual value (with struct)

	On sqlite and mysql, native unsigned bigint types are used. In all cases, the
	value we deal with in python is always in hex.
	"""
	def db_type(self, connection):
		engine = connection.settings_dict["ENGINE"]
		if engine == "django.db.backends.mysql":
			return "bigint unsigned"
		elif engine == "django.db.backends.sqlite":
			return "UNSIGNED BIG INT"
		else:
			return super(HexIntegerField, self).db_type(connection)

	def get_prep_value(self, value):
		if value is None or value == "":
			return None
		if isinstance(value, six.string_types):
			value = int(value, 16)
		# on postgres only, interpret as signed
		if connection.settings_dict["ENGINE"] in postgres_engines:
			value = struct.unpack("q", struct.pack("Q", value))[0]
		return value

	def to_python(self, value):
		if isinstance(value, six.string_types):
			return value
		if value is None:
			return ""
		# on postgres only, re-interpret from signed to unsigned
		if connection.settings_dict["ENGINE"] in postgres_engines:
			value = hex(struct.unpack("Q", struct.pack("q", value))[0])
		return value

	def formfield(self, **kwargs):
		defaults = {"form_class": HexadecimalField}
		defaults.update(kwargs)
		# yes, that super call is right
		return super(models.IntegerField, self).formfield(**defaults)

try:
	from south.modelsinspector import add_introspection_rules
	add_introspection_rules([], ["^push_notifications\.fields\.HexIntegerField"])
except ImportError:
	pass
