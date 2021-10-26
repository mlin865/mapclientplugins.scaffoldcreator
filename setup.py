from setuptools import setup, find_packages
from setuptools.command.install import install
import os
import io

SETUP_DIR = os.path.dirname(os.path.abspath(__file__))

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
    "scaffoldmaker @ https://api.github.com/repos/ABI-Software/scaffoldmaker/tarball/main",
    "opencmiss.maths",
    "opencmiss.utils >= 0.3",
    "opencmiss.zinc > 3.2",
    "opencmiss.zincwidgets >= 2.0",
    "PySide2"
]
source_license = readfile("LICENSE")


class InstallCommand(install):

    def run(self):
        install.run(self)
        # Automatically install requirements from requirements.txt
        import subprocess
        subprocess.call(['pip', 'install', '-r', os.path.join(SETUP_DIR, 'requirements.txt')])


setup(
    name='mapclientplugins.meshgeneratorstep',
    version='0.1.1',
    description='',
    long_description='\n'.join(readme) + source_license,
    classifiers=[
      "Development Status :: 3 - Alpha",
      "License :: OSI Approved :: Apache Software License",
      "Programming Language :: Python",
    ],
    cmdclass={'install': InstallCommand,},
    author='Richard Christie',
    author_email='',
    url='https://github.com/ABI-Software/mapclientplugins.meshgeneratorstep',
    license='APACHE',
    packages=find_packages(exclude=['ez_setup',]),
    namespace_packages=['mapclientplugins'],
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    )
