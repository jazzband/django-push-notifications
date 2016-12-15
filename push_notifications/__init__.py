import sys

__author__ = "Jerome Leclanche"
__email__ = "jerome@leclan.ch"
__version__ = "1.4.1"


class NotificationError(Exception):
    pass


if sys.version_info.major > 2:
    def decodestr(s):
        return s
else:
    def decodestr(s):
        return s.decode('utf-8')
