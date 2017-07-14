from __future__ import absolute_import, division, print_function

import os
import sys
import site

# This is used for message definitions, not for python code
site.addsitedir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'rosdeps'))

import rosimport
rosimport.activate()
