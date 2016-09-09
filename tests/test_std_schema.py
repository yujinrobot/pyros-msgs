from __future__ import absolute_import
from __future__ import print_function


import requests
import functools
import marshmallow

import pyros_msgs.msg as pyros_msgs
import std_msgs.msg as std_msgs


# Testing serialization / deserialization of basic ROS message types


class TestRosBoolSchema(marshmallow.Schema):
    """
    Schema to test RosBool Field

    >>> schema = TestRosBoolSchema()

    >>> rosmsgTrue = std_msgs.Bool(True)
    >>> marshalledTrue = schema.dump(rosmsgTrue)
    >>> marshmallow.pprint(marshalledTrue.data)
    {u'data': True}
    >>> value, errors = schema.load(marshalledTrue.data)
    >>> print(value) if not errors:
    {'data': True}

    >>> rosmsgFalse = std_msgs.Bool(False)
    >>> marshalledFalse, errors = schema.dump(rosmsgFalse)
    >>> marshmallow.pprint(marshalledFalse.data) if not errors else print("FAILED !")
    {u'data': False}
    >>> value, errors = schema.load(marshalledFalse.data)
    >>> isinstance(value, std_msgs.Bool) if not errors else print("FAILED !")
    True
    >>> print(value) if not errors else print("FAILED !")
    {'data': False}

    Easy conversion from Ros Type to pure python is done like this :
    >>> defaultRosBool = std_msgs.Bool()
    >>> schema.load(schema.dump(defaultRosBool))

    Load is the inverse of dump:
    >>> randomRosBool = std_msgs.Bool(random.choice([True, False]))
    >>> schema.load(schema.dump(randomRosBool)) == randomRosBool


    """
    data = pyros_msgs.RosBool()

