#!/usr/bin/env python
from StringIO import StringIO

import os.path
from distutils.core import setup
from setuptools.command.test import test as TestCommand
import sys

README = open(os.path.join(os.path.dirname(__file__), "README.rst")).read()

CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Environment :: Web Environment",
    "Framework :: Django",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Networking",
]

VERSION = "0.8"

tests_require = [
    'pytest',
    'pep8',
]


class PushNotificationsTest(TestCommand):
    def finalize_options(self):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")
        import test_settings
        from django.core.management import call_command
        db_file = test_settings.DATABASES.get('default').get('NAME')
        if os.path.exists(db_file):
            os.unlink(db_file)

        call_command('syncdb', interactive=False)
        call_command('flush', interactive=False)

        TestCommand.finalize_options(self)
        self.test_args = ['tests']
        self.test_suite = True
        self.packages = self.resolve_packages()

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

    def resolve_packages(self):
        """
        Frame hack to determine packages contained in module for testing.
        We ignore submodules (those containing '.')
        """
        f = sys._getframe()
        while f:
            if 'self' in f.f_locals:
                locals_self = f.f_locals['self']
                py_modules = getattr(locals_self, 'py_modules', None)
                packages = getattr(locals_self, 'packages', None)

                top_packages = []
                if py_modules or packages:
                    if py_modules:
                        for module in py_modules:
                            if '.' not in module:
                                top_packages.append(module)
                    if packages:
                        for package in packages:
                            if '.' not in package:
                                top_packages.append(package)

                    return list(set(top_packages))
            f = f.f_back

    def pep8_report(self):
        """
        Outputs PEP8 report to screen and pep8.txt.
        """
        verbose = '--quiet' not in sys.argv
        if verbose:
            import pep8
            # Hook into stdout.
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()

            # Run Pep8 checks, excluding South migrations.
            pep8_style = pep8.StyleGuide()
            pep8_style.options.exclude.append('migrations')
            pep8_style.check_files(self.packages)

            # Restore stdout.
            sys.stdout = old_stdout

            # Save result to pep8.txt.
            result = mystdout.getvalue()
            output = open('pep8.txt', 'w')
            output.write(result)
            output.close()

            # Return Pep8 result
            if result:
                print("\nPEP8 Report:")
                print(result)

    def run(self):
        self.pep8_report()
        TestCommand.run(self)


setup(
    name="django-push-notifications",
    packages=["push_notifications"],
    author="Jerome Leclanche",
    author_email="jerome.leclanche+pypi@gmail.com",
    classifiers=CLASSIFIERS,
    description="Send push notifications to mobile devices through GCM or APNS in Django.",
    download_url="https://github.com/Adys/django-push-notifications/tarball/master",
    long_description=README,
    url="https://github.com/Adys/django-push-notifications",
    version=VERSION,
    tests_require=tests_require,
    cmdclass={'test': PushNotificationsTest},
)
