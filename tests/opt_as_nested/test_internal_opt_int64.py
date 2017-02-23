from __future__ import absolute_import
from __future__ import print_function

try:
    import genpy
    from pyros_msgs.opt_as_nested import opt_int64
    from pyros_msgs.common import ros_python_default_mapping  # just for testing
except ImportError:
    # Because we need to access Ros message types here (from ROS env or from virtualenv, or from somewhere else)
    import pyros_setup
    # We rely on default configuration to point us ot the proper distro
    pyros_setup.configurable_import().configure().activate()
    import genpy
    from pyros_msgs.opt_as_nested import opt_int64
    from pyros_msgs.common import ros_python_default_mapping  # just for testing

import nose


def test_init_data_internal():
    msg = opt_int64(data=42)
    assert msg.initialized_ is True
    assert msg.data == 42


def test_init_default_internal():
    msg = opt_int64()
    assert msg.initialized_ is False
    assert msg.data == ros_python_default_mapping['int64']


def test_reset_default_internal():
    opt_int64.reset_default(23)
    msg = opt_int64()
    assert msg.initialized_ is False
    assert msg.data == 23
    opt_int64.reset_default()
    msg = opt_int64()
    assert msg.initialized_ is False
    assert msg.data == ros_python_default_mapping['int64']


def test_force_init_excepts_internal():
    with nose.tools.assert_raises(AttributeError) as cm:
        opt_int64(initialized_=True)
    assert cm.exception.message == "The field 'initialized_' is an internal field of pyros_msgs/opt_int64 and should not be set by the user."


# Just in case we run this directly
if __name__ == '__main__':
    nose.runmodule(__name__)
