from __future__ import absolute_import, division, print_function

# This is a namespace package to merge the ROS generated messages and the python subpackage sources
# Note : this file must be loaded first in order for other subpackages to be found
# Note : this works for development packages only if pyros_setup has been activated
#        because it will put egg directories on pythonpath FIRST.

# pkgutil does not seem, somehow, to be compatible with ROS devel space...
# import pkgutil
# __path__ = pkgutil.extend_path(__path__, __name__)

# Be aware : https://github.com/jonparrott/namespace-pkg-tests/blob/master/table.md
import pkg_resources
pkg_resources.declare_namespace(__name__)
