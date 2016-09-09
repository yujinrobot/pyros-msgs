
# Because we need to access Ros message types here (from ROS env or from virtualenv, or from somewhere else)
import pyros_setup
# We rely on default configuration to point us ot the proper distro
pyros_setup.configurable_import().configure().activate()


from .decorators import wraps_cls, with_field_validation, with_schema_validation, with_factorymethod_on_deserialize
from .std_bool import RosFieldBool, RosMsgBool
from .std_int import (
    RosFieldInt8, RosFieldInt16, RosFieldInt32, RosFieldInt64, RosFieldUInt8, RosFieldUInt16, RosFieldUInt32, RosFieldUInt64,
    RosMsgInt8, )
#from .std_float import R
from .decorators import *

__all__ = [

]