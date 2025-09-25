import sys
import warnings

try:
    # Python 3.8+
    import importlib.metadata as importlib_metadata
except ImportError:
    # <Python 3.7 and lower
    import importlib_metadata

if sys.version_info < (3, 10):
    warnings.warn(
        "Python 3.9 and earlier support is deprecated and will be removed in a future version. "
        "Please upgrade to Python 3.10 or later.",
        UserWarning,
        stacklevel=2
    )

__version__ = importlib_metadata.version("django-push-notifications")
