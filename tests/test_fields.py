from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from push_notifications.fields import HexadecimalField


class HexadecimalFieldTestCase(SimpleTestCase):
	_INVALID_HEX_VALUES = [
		"foobar",
		"GLUTEN",
		"HeLLo WoRLd",
		"international",
		"°!#€%&/()[]{}=?",
		"0x",
	]

	_VALID_HEX_VALUES = {
		"babe": "babe",
		"BEEF": "BEEF",
		" \nfeed \t": "feed",
		"0x012345789abcdef": "0x012345789abcdef",
		"012345789aBcDeF": "012345789aBcDeF",
	}

	def test_clean_invalid_values(self):
		"""Passing invalid values raises ValidationError."""
		f = HexadecimalField()
		for invalid in self._INVALID_HEX_VALUES:
			self.assertRaisesMessage(
				ValidationError,
				"'Enter a valid hexadecimal number'",
				f.clean,
				invalid,
			)

	def test_clean_valid_values(self):
		"""Passing valid values returns the expected output."""
		f = HexadecimalField()
		for valid, expected in self._VALID_HEX_VALUES.items():
			self.assertEqual(expected, f.clean(valid))
