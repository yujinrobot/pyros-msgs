from __future__ import absolute_import
from __future__ import print_function

from .msg import (
    # no slot
    # None

    # data slot
    opt_empty,

    opt_bool,
    opt_int8, opt_int16, opt_int32, opt_int64,
    opt_uint8, opt_uint16, opt_uint32, opt_uint64,
    opt_float32, opt_float64,
    opt_string,

    opt_time,
    opt_duration,
    opt_header,

    # multiple slots
    # None
)


def duck_punch(msg_mod):
    def init_punch(self, *args, **kwds):
        __doc__ = msg_mod.__init__.__doc__
        # excepting when passing initialized_. it is meant to be an internal field.
        if 'initialized_' in kwds.keys():
            raise AttributeError("The field 'initialized_' is an internal field of {0} and should not be set by the user.".format(msg_mod._type))
        if args or kwds:
            super(msg_mod, self).__init__(*args, **kwds)
            # initialized value depends on all field assigned
            if self.data is None:
                self.data = False
                self.initialized_ = False
            else:
                self.initialized_ = True
        else:
            self.initialized_ = False
            self.data = False

    # duck punching into genpy generated message classes, to set initialized_ field properly
    msg_mod.__init__ = init_punch


for msg_mod in [
    opt_empty,
    opt_bool,
    opt_int8, opt_int16, opt_int32, opt_int64,
    opt_uint8, opt_uint16, opt_uint32, opt_uint64,
    opt_float32, opt_float64,
    opt_string,
    opt_time,
    opt_duration,
    opt_header,
]:
    duck_punch(msg_mod)
