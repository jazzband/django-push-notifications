#!/usr/bin/env python
from setuptools import setup
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.rst").read_text()
setup(
    long_description=long_description,
    long_description_content_type='text/x-rst',
    use_scm_version={"version_scheme": "post-release"}
)
