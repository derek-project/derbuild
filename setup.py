import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "derbuild",
    version = "0.0.1",
    author = "Dmitry Rozhkov",
    author_email = "dmitry.rojkov@gmail.com",
    description = ("Build scripts."),
    license = "GPL",
    keywords = "build cross-compilation",
    url = "http://packages.python.org/an_example_pypi_project",
    packages = ['derbuild'],
    install_requires = [],
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GPL License",
    ],
    entry_points={
        'console_scripts':
            [
                'derbuild = derbuild.cli:main'
            ],
        'srcpkgs':
            [
                'application/x-debian-source-control = derbuild.debpackage:DebPackage',
                'application/x-redhat-package-manager = derbuild.rpmpackage:RpmPackage'
            ]
    },
    test_suite = "tests",
    tests_require = ['mock>=0.8.0']
)
