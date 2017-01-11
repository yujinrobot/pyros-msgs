from __future__ import absolute_import
from __future__ import print_function

import sys
import six

# Utility functions

# Ref : http://wiki.ros.org/msg
if sys.version_info >= (3, 0):
    ros_python_type_mapping = {
        'bool': bool,
        'int8': int, 'int16': int, 'int32': int, 'int64': int,
        'uint8': int, 'uint16': int, 'uint32': int, 'uint64': int,
        'float32': float, 'float64': float,
        'string': str,  # CAREFUL between ROS who wants byte string, and python3 where everything is unicode...
        #'string': RosTextString,  # CAREFUL between ROS who wants byte string, and python3 where everything is unicode...
        # Time ???
    }
else:  # 2.7
    ros_python_type_mapping = {
        'bool': bool,
        'int8': int, 'int16': int, 'int32': int, 'int64': long,
        'uint8': int, 'uint16': int, 'uint32': int, 'uint64': long,
        'float32': float, 'float64': float,
        'string': str,  # CAREFUL between ROS who wants byte string, and python3 where everything is unicode...
        #'string': RosTextString,  # CAREFUL between ROS who wants byte string, and python3 where everything is unicode...
        # Time ???
    }

ros_python_default_mapping = {
    'bool': False,
    'int8': 0, 'uint8': 0, 'int16': 0, 'uint16': 0, 'int32': 0, 'uint32': 0, 'int64': 0, 'uint64': 0,
    'float32': 0.0, 'float64': 0.0,
    'string': '',
    'time': 0,
    'duration': 0,
}

__all__ = [
    'ros_python_type_mapping',
    'ros_python_default_mapping'
]