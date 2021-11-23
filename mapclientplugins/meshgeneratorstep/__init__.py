
"""
MAP Client Plugin
"""

__version__ = '0.3.0'
__author__ = 'Richard Christie'
__stepname__ = 'Mesh Generator'
__location__ = 'https://github.com/ABI-Software/mapclientplugins.meshgeneratorstep'

# import class that derives itself from the step mountpoint.
from mapclientplugins.meshgeneratorstep import step

# Import the resource file when the module is loaded,
# this enables the framework to use the step icon.
from . import resources_rc
