from __future__ import absolute_import, division, print_function

import os
import sys


import pytest

# TODO : find a better place for this ?
from pyros_msgs.importer.rosmsg_generator import MsgDependencyNotFound, generate_msgsrv_nspkg, import_msgsrv

try:
    # a dynamically generated message type just for testing...
    generated_modules = generate_msgsrv_nspkg(
        [os.path.join(os.path.dirname(__file__), 'msg', 'test_opt_std_empty_as_array.msg')],
        dependencies=['std_msgs'],
        # this is needed to be able to run this without underlying ROS system setup
        include_path=['std_msgs:' + os.path.join(os.path.dirname(__file__), 'msg', 'std_msgs')],
    )
    for m in generated_modules:
        import_msgsrv(m)

except MsgDependencyNotFound:
    pytest.skip("Failed to find message package std_msgs.")


test_opt_std_empty_as_array = getattr(sys.modules['gen_msgs.msg._test_opt_std_empty_as_array'], 'test_opt_std_empty_as_array')


import pyros_msgs.opt_as_array
# patching (need to know the field name)
pyros_msgs.opt_as_array.duck_punch(test_opt_std_empty_as_array, ['data'])

import hypothesis
import hypothesis.strategies


try:
    # First we try to import from environment
    from std_msgs.msg import Empty as std_msgs_Empty

except ImportError:
    # If we cannot import messages from environment (happens in isolated python usecase) we can try to generate them
    generated_modules = generate_msgsrv_nspkg(
        [os.path.join(os.path.dirname(__file__), 'msg', 'std_msgs', 'Empty.msg')],
        package='std_msgs'
    )
    for m in generated_modules:
        import_msgsrv(m)

    std_msgs_Empty = getattr(sys.modules['std_msgs.msg._Empty'], 'Empty')

    # pytest.skip("Cannot import std_msgs.msg")


@hypothesis.given(hypothesis.strategies.lists(hypothesis.strategies.builds(std_msgs_Empty), max_size=1))
def test_init_rosdata(data):
    msg = test_opt_std_empty_as_array(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.builds(std_msgs_Empty))
def test_init_data(data):
    msg = test_opt_std_empty_as_array(data=data)
    assert msg.data == [data]


@hypothesis.given(hypothesis.strategies.builds(std_msgs_Empty))
def test_init_raw(data):
    msg = test_opt_std_empty_as_array(data)
    assert msg.data == [data]


def test_init_default():
    msg = test_opt_std_empty_as_array()
    assert msg.data == []


# Just in case we run this directly
if __name__ == '__main__':
    pytest.main(['-s', __file__])
