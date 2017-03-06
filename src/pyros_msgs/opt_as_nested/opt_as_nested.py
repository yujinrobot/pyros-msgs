from __future__ import absolute_import
from __future__ import print_function

import collections

import genpy
import six
import std_msgs.msg
from pyros_msgs.common import (
    validate_type,
    get_accepted_typeschema_from_type,
    get_generated_typeschema_from_type,
    get_default_val_from_type,

    get_default_val_from_opt_nested_type
)


def duck_punch(msg_mod, opt_slot_list):
    """
    Duck punch / monkey patch msg_mod, by declaring slots in opt_slot_list as optional slots
    :param msg_mod:
    :param opt_slot_list:
    :return:
    """
    def init_punch(self, *args, **kwds):
        __doc__ = msg_mod.__init__.__doc__

        if args:  # the args for super(msg_mod, self) are fixed to the slots in ros messages
            # so we can change it to kwarg to be more accepting (and more robust for changes)
            kwds.update(zip([s for s in self.__slots__], args))
            args = ()

        # Validating arg type (we should be more strict than ROS.)
        for s, st in [(_slot, _slot_type) for _slot, _slot_type in zip(self.__slots__, self._slot_types)]:

            if st.startswith('pyros_msgs/opt_'):
                if kwds and kwds.get(s) is not None:
                    try:
                        # This will convert the type if necessary
                        sv = validate_type(kwds.get(s), st)
                    except TypeError as te:
                        sv = kwds.get(s)
                        raise AttributeError("field {s} has value {sv} which is not of expected type {st}".format(**locals()))
                else:
                    # Here we build the default optional type (uninitialized)
                    kwds[s] = get_default_val_from_opt_nested_type(st)

            else:  # not an optional field, but we still need to validate the type
                if kwds and s in kwds:
                    kwds[s] = validate_type(kwds.get(s), st)
                # else it will be set to None by parent class (according to original ROS message behavior)

        # By now the kwds is filled up with values
        # the parent init will do the usual ROS message setup.
        super(msg_mod, self).__init__(*args, **kwds)

        # We follow the usual ROS generated message behavior and assign default values
        for s, st in [(_slot, _slot_type) for _slot, _slot_type in zip(self.__slots__, self._slot_types)]:
            if getattr(self, s) is None:
                setattr(self, s, get_default_val_from_type(st))

    # duck punching into genpy generated message classes.
    msg_mod.__init__ = init_punch

    # Registering the list of optional field (required by pyros_schemas)
    msg_mod._opt_slots = opt_slot_list
