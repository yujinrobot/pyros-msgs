from __future__ import absolute_import
from __future__ import print_function

try:
    import genpy
    from pyros_msgs.opt_as_nested import opt_int8
except ImportError:
    # Because we need to access Ros message types here (from ROS env or from virtualenv, or from somewhere else)
    import pyros_setup
    # We rely on default configuration to point us ot the proper distro
    pyros_setup.configurable_import().configure().activate()
    import genpy
    from pyros_msgs.opt_as_nested import opt_int8

import nose


def test_init_data():
    msg = opt_int8(data=42)
    assert msg.initialized_ is True
    assert msg.data == 42


def test_init_default():
    msg = opt_int8()
    assert msg.initialized_ is False


def test_force_init_excepts():
    with nose.tools.assert_raises(AttributeError) as cm:
        opt_int8(initialized_=True)
    assert cm.exception.message == "The field 'initialized_' is an internal field of pyros_msgs/opt_int8 and should not be set by the user."


# Just in case we run this directly
if __name__ == '__main__':
    nose.runmodule(__name__)
