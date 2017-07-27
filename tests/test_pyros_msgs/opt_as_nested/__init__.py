from __future__ import absolute_import, division, print_function

import os
import sys
import site

# This is used for message definitions, not for python code
site.addsitedir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'rosdeps'))

# Using genpy directly if ROS has been setup (while using from ROS pkg)
import genpy, genmsg

import rosimport
rosimport.activate()
