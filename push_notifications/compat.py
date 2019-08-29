# flake8:noqa

try:
	from urllib.error import HTTPError
	from urllib.parse import urlencode
	from urllib.request import Request, urlopen
except ImportError:
	# Python 2 support
	from urllib2 import HTTPError, Request, urlopen
	from urllib import urlencode
