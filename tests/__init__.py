from .test_models import *
from .test_gcm_push_payload import *
from .test_apns_push_payload import *
from .test_management_commands import *
from .test_apns_certfilecheck import *
from .test_wns import *

# conditionally test rest_framework api if the DRF package is installed
try:
	import rest_framework
except ImportError:
	pass
else:
	from test_rest_framework import *
