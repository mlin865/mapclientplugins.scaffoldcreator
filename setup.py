import codecs
import io
import os
import re

from setuptools import setup, find_packages

SETUP_DIR = os.path.dirname(os.path.abspath(__file__))


def read(*parts):
    with codecs.open(os.path.join(SETUP_DIR, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# List all of your Python package dependencies in the
# requirements.txt file


def readfile(filename, split=False):
    with io.open(filename, encoding="utf-8") as stream:
        if split:
            return stream.read().split("\n")
        return stream.read()


readme = readfile("README.rst", split=True)[3:]  # skip title
# For requirements not hosted on PyPi place listings
# into the 'requirements.txt' file.
requires = [
    # minimal requirements listing
    "scaffoldmaker >= 0.8",
    "opencmiss.maths",
    "opencmiss.utils >= 0.3",
    "opencmiss.zinc >= 3.10.2",
    "opencmiss.zincwidgets >= 2.0",
    "PySide2"
]
source_license = readfile("LICENSE")

setup(
    name='mapclientplugins.scaffoldcreator',
    version=find_version('mapclientplugins', 'scaffoldcreator', '__init__.py'),
    description='MAP Client plugin for generating meshes via scripts using OpenCMISS-Zinc.',
    long_description='\n'.join(readme) + source_license,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
    ],
    author='Richard Christie',
    author_email='',
    url='https://github.com/ABI-Software/mapclientplugins.scaffoldcreator',
    license='APACHE',
    packages=find_packages(exclude=['ez_setup', ]),
    namespace_packages=['mapclientplugins'],
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
)
