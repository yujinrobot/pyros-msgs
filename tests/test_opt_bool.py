from __future__ import absolute_import
from __future__ import print_function

try:
    import genpy
    import pyros_msgs

except ImportError:
    # Because we need to access Ros message types here (from ROS env or from virtualenv, or from somewhere else)
    import pyros_setup
    # We rely on default configuration to point us ot the proper distro
    pyros_setup.configurable_import().configure().activate()
    import genpy
    import pyros_msgs

import nose


def test_init_data():
    msg = pyros_msgs.opt_bool(data=True)
    assert msg.initialized_ is True
    assert msg.data is True

    msg = pyros_msgs.opt_bool(data=False)
    assert msg.initialized_ is True
    assert msg.data is False


def test_init_default():
    msg = pyros_msgs.opt_bool()
    assert msg.initialized_ is False


def test_force_init_excepts():
    with nose.tools.assert_raises(AttributeError) as cm:
        pyros_msgs.opt_bool(initialized_=True)
    assert cm.exception.message == "The field 'initialized_' is an internal field of pyros_msgs/opt_bool and should not be set by the user."


# Just in case we run this directly
if __name__ == '__main__':
    nose.runmodule(__name__)
