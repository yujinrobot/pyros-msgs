from __future__ import absolute_import, division, print_function

import os
import six
import sys
import numpy
import pytest
import collections
from six import BytesIO, StringIO

import site
# This is used for message definitions, not for python code
site.addsitedir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'rosdeps'))

import rosimport
rosimport.activate()

# This should succeed if the message class was already generated
import std_msgs.msg as std_msgs

import genpy

from pyros_msgs.typecheck.typechecker import (
    six_long,
    maybe_list,
    maybe_tuple,
    Sanitizer, Accepter, Array, Any, MinMax,
    TypeChecker,
    TypeCheckerException,
)

from pyros_msgs.typecheck.ros_mappings import typechecker_from_rosfield_type


from hypothesis import given, example, settings, Verbosity
import hypothesis.strategies as st


# The main point here is insuring that any sanitized type will safely serialize and deserialize
# And also that any type that doesnt safely serialize / deserialize will not pass the type checker

rosmsg_slot_types = [
    ('bool', st.booleans()),
    ('int', st.integers()),
    ('float', st.floats()),
    ('string', st.binary()),
    ('time', st.builds(genpy.Time, secs=st.integers(min_value=0), nsecs=st.integers(min_value=0))),  # ROS time
    ('duration', st.builds(genpy.Duration, secs=st.integers(), nsecs=st.integers())),  # ROS duration
]

rosmsg_slot_arraytypes = [
    (s[0] + '[]',  st.lists(elements=s[1]))
    for s in rosmsg_slot_types
]

# TODO : is there a way to generate messages on the fly to test all possible field combinations ?

# For now We use a set of basic messages for testing
std_msgs_types_strat_ok = collections.OrderedDict([
    ('std_msgs/Bool', st.builds(std_msgs.Bool, data=st.booleans())),
    ('std_msgs/Int8', st.builds(std_msgs.Int8, data=st.one_of(st.booleans(), st.integers(min_value=-128, max_value=127)))),  # in python booleans are integers
    ('std_msgs/Int16', st.builds(std_msgs.Int16, data=st.one_of(st.booleans(), st.integers(min_value=-32768, max_value=32767)))),
    ('std_msgs/Int32', st.builds(std_msgs.Int32, data=st.one_of(st.booleans(), st.integers(min_value=-2147483648, max_value=2147483647)))),
    ('std_msgs/Int64', st.builds(std_msgs.Int64, data=st.one_of(st.booleans(), st.integers(min_value=-six_long(9223372036854775808), max_value=six_long(9223372036854775807))))),
    ('std_msgs/UInt8', st.builds(std_msgs.UInt8, data=st.one_of(st.booleans(), st.integers(min_value=0, max_value=255)))),
    ('std_msgs/UInt16', st.builds(std_msgs.UInt16, data=st.one_of(st.booleans(), st.integers(min_value=0, max_value=65535)))),
    ('std_msgs/UInt32', st.builds(std_msgs.UInt32, data=st.one_of(st.booleans(), st.integers(min_value=0, max_value=4294967295)))),
    ('std_msgs/UInt64', st.builds(std_msgs.UInt64, data=st.one_of(st.booleans(), st.integers(min_value=0, max_value=six_long(18446744073709551615))))),
    # TMP : seems we have some problems with float arithmetic between numpy and hypothesis...
    #'std_msgs/Float32': st.builds(std_msgs.Float32, data=st.floats(min_value=-3.4028235e+38, max_value=3.4028235e+38)),
    #'std_msgs/Float64': st.builds(std_msgs.Float64, data=st.floats(min_value=-1.7976931348623157e+308, max_value=1.7976931348623157e+308, )),
    #'std_msgs/String': st.builds(std_msgs.String, data=st.one_of(st.binary(), st.text(alphabet=st.characters(max_codepoint=127)))),
    ('std_msgs/String', st.builds(std_msgs.String, data=st.text(alphabet=st.characters(max_codepoint=127)))),  # binary can break hypothesis reporting
    # CAREFUL : we need to avoid having nsecs making our secs overflow after canonization from __init__
    ('std_msgs/Time', st.builds(std_msgs.Time, data=st.builds(genpy.Time, secs=st.integers(min_value=0, max_value=4294967295 -3), nsecs=st.integers(min_value=0, max_value=4294967295)))),
    ('std_msgs/Duration', st.builds(std_msgs.Duration, data=st.builds(genpy.Duration, secs=st.integers(min_value=-2147483648 +1, max_value=2147483647 -1), nsecs=st.integers(min_value=-2147483648, max_value=2147483647)))),
    # TODO : add more. we should test all.
])

std_msgs_types_strat_broken = collections.OrderedDict([
    # everything else...
    ('std_msgs/Bool', st.builds(std_msgs.Bool, data=st.one_of(st.integers(), st.floats()))),
    ('std_msgs/Int8', st.builds(std_msgs.Int8, data=st.one_of(st.floats(), st.integers(min_value=127+1), st.integers(max_value=-128-1)))),
    ('std_msgs/Int16', st.builds(std_msgs.Int16, data=st.one_of(st.floats(), st.integers(min_value=32767+1), st.integers(max_value=-32768-1)))),
    ('std_msgs/Int32', st.builds(std_msgs.Int32, data=st.one_of(st.floats(), st.integers(min_value=2147483647+1), st.integers(max_value=-2147483648-1)))),
    ('std_msgs/Int64', st.builds(std_msgs.Int64, data=st.one_of(st.floats(), st.integers(min_value=six_long(9223372036854775807+1)), st.integers(max_value=six_long(-9223372036854775808-1))))),
    ('std_msgs/UInt8', st.builds(std_msgs.UInt8, data=st.one_of(st.floats(), st.integers(min_value=255+1), st.integers(max_value=-1)))),
    ('std_msgs/UInt16', st.builds(std_msgs.UInt16, data=st.one_of(st.floats(), st.integers(min_value=65535+1), st.integers(max_value=-1)))),
    ('std_msgs/UInt32', st.builds(std_msgs.UInt32, data=st.one_of(st.floats(), st.integers(min_value=4294967295+1), st.integers(max_value=-1)))),
    ('std_msgs/UInt64', st.builds(std_msgs.UInt64, data=st.one_of(st.floats(), st.integers(min_value=six_long(18446744073709551615+1)), st.integers(max_value=-1)))),
    ('std_msgs/Float32', st.builds(std_msgs.Float32, data=st.one_of(st.booleans(), st.integers()))),  # st.floats(max_value=-3.4028235e+38), st.floats(min_value=3.4028235e+38))),
    ('std_msgs/Float64', st.builds(std_msgs.Float64, data=st.one_of(st.booleans(), st.integers()))),  # st.floats(max_value=-1.7976931348623157e+308), st.floats(min_value=1.7976931348623157e+308))),
    # TODO : add more. we should test all
])

pyros_msgs_types_strat_ok = {
    # TODO
}

pyros_msgs_types_strat_broken = {

}

# We need a composite strategy to link slot type and slot value
@st.composite
@settings(verbosity=Verbosity.verbose, timeout=1)
def msg_type_and_value(draw, msgs_type_st):
    msg_type = draw(st.sampled_from(msgs_type_st))
    msg_value = draw(msgs_type_st.get(msg_type))
    return msg_type, msg_value


@given(msg_type_and_value(std_msgs_types_strat_ok))
@settings(verbosity=Verbosity.verbose, timeout=1)
def test_typechecker_serialize_deserialize_inverse(msg_type_and_ok_value):
    """"""
    tc = typechecker_from_rosfield_type(msg_type_and_ok_value[0])
    value = tc(msg_type_and_ok_value[1])

    # sending
    buff = BytesIO()
    value.serialize(buff)
    serialized = buff.getvalue()
    buff.close()

    # receiving
    received = tc()
    received.deserialize(serialized)

    if isinstance(value, std_msgs.Float64):  # for floats, this is only true relative to some epsilon...
        numpy.testing.assert_allclose(received.data, value.data)
    elif isinstance(value, std_msgs.Float32):  # for floats, this is only true relative to some epsilon...
        numpy.testing.assert_allclose(received.data, value.data, rtol=1e-5)
    else:
        assert received == msg_type_and_ok_value[1]


@given(msg_type_and_value(std_msgs_types_strat_broken))
@settings(verbosity=Verbosity.verbose, timeout=1)
def test_typechecker_typechecker_prevent_broken_values(msg_type_and_bad_value):
    tc = typechecker_from_rosfield_type(msg_type_and_bad_value[0])

    # assert we have a somehow broken value :
    with pytest.raises(Exception) as excinfo:
        value = tc(msg_type_and_bad_value[1])

        # sending
        buff = BytesIO()
        value.serialize(buff)
        serialized = buff.getvalue()
        buff.close()

        # receiving
        received = tc()
        received.deserialized(serialized)

    # assert the type checker doesnt accept it
    with pytest.raises(TypeCheckerException) as excinfo:
        _ = tc(msg_type_and_bad_value[1])
    assert 'is not accepted' in excinfo.value.message
