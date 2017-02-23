from __future__ import absolute_import
from __future__ import print_function

import sys

try:
    import pyros_msgs.opt_as_array  # This will duck punch the standard message type initialization code.
    from pyros_msgs.msg import test_opt_int64_as_array  # a message type just for testing
except ImportError:
    # Because we need to access Ros message types here (from ROS env or from virtualenv, or from somewhere else)
    import pyros_setup
    # We rely on default configuration to point us ot the proper distro
    pyros_setup.configurable_import().configure().activate()
    import pyros_msgs.opt_as_array  # This will duck punch the standard message type initialization code.
    from pyros_msgs.msg import test_opt_int64_as_array  # a message type just for testing

# patching
pyros_msgs.opt_as_array.duck_punch(test_opt_int64_as_array, ['data'])

import nose

if sys.version_info >= (3, 0):
    test_val = 42
else:  # 2.7
    test_val = 42L  # because we enforce long in message we need to validate with a long value


def test_init_rosdata():
    msg = test_opt_int64_as_array(data=[test_val])
    assert msg.data == [test_val]


def test_init_data():
    msg = test_opt_int64_as_array(data=test_val)
    assert msg.data == [test_val]


def test_init_raw():
    msg = test_opt_int64_as_array(test_val)
    assert msg.data == [test_val]


def test_init_default():
    msg = test_opt_int64_as_array()
    assert msg.data == []


# Just in case we run this directly
if __name__ == '__main__':
    nose.runmodule(__name__)
