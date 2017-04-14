from __future__ import absolute_import, division, print_function

import pyros_msgs

from pyros_msgs.typecheck import (
    six_long,
    TypeCheckerException,
    typechecker_from_rosfield_type,
    TypeChecker,
    make_typechecker_field_optional,
    make_typechecker_field_hidden,
)

import os
import sys


from .ros_mappings import typechecker_from_rosfield_opttype


def duck_punch(msg_mod, opt_slot_list):
    """
    Duck punch / monkey patch msg_mod, by declaring slots in opt_slot_list as optional slots
    :param msg_mod:
    :param opt_slot_list:
    :return:
    """

    # Delayed import to look for generated OptionalFields just before using it.
    # Trick to be able to import this package without requiring messages to be generated yet (like for opt_as_array).
    # This allow on the fly generation for subpackages (like .tests).
    try:
        from pyros_msgs.msg import OptionalFields
    except ImportError:  # if we fail here, we can attempt to generate on the fly
        print(
            "OptionalFields has not been found in pyros_msgs.msg subpackage. Make sure you run 'python setup.py generate' before using this package.")
        raise

    def get_settable_fields():
        return {s: st for s, st in zip(msg_mod.__slots__, msg_mod._slot_types) if st != 'pyros_msgs/OptionalFields'}

    def get_optfields_field():
        optfields = {s: st for s, st in zip(msg_mod.__slots__, msg_mod._slot_types) if st == 'pyros_msgs/OptionalFields'}
        if len(optfields) > 1:
            raise AttributeError(
                "Only one field of type 'pyros_msgs/OptionalFields' is needed. Currently the message {msg_mod._type} has multiple fields of that type : {optfields}".format(
                    **locals()))
        if len(optfields) < 1:
            raise AttributeError(
                "The Message Type {msg_mod._type} should contain a field of type 'pyros_msgs/OptionalFields' which will be automatically populated.".format(
                    **locals()))
        return optfields

    def init_punch(self, *args, **kwds):
        __doc__ = msg_mod.__init__.__doc__

        settable_slots = get_settable_fields()

        if args:  # the args for super(msg_mod, self) are fixed to the slots in ros messages
            # so we can change it to kwarg to be more accepting (and more robust for changes)
            kwds.update(zip(settable_slots, args))
            args = ()

        optfields = get_optfields_field()

        for f in optfields:
            if f in kwds:
                raise AttributeError(" the field {opt_f[0]} will be automatically managed and should not be set when constructing the message.".format(**locals()))

        # We build our own type schema here from our slots
        # CAREFUL : slot discovery doesnt work well with inheritance -> fine since ROS msgs do not have any inheritance concept.
        slotsdict = {
            s: typechecker_from_rosfield_opttype(srt)
            for s, srt in settable_slots.items()
        }

        # Modifying typechecker to accept None for optional types
        for s, st in slotsdict.items():
            if s in opt_slot_list:
                slotsdict[s] = make_typechecker_field_optional(st)

        # TODO : use accepted typeschema to filter args

        # TODO : use type schema method to build this instance

        # We assign slots one by one after verifying and sanitizing the type
        for s, st in slotsdict.items():
            # check all slots values passed in kwds.
            # We DO NOT assign default values here (nested type should manage default values for fields)
            sval = kwds.get(s)
            try:
                if sval is not None:
                    kwds[s] = st(sval)
            except TypeCheckerException as tse:
                # TODO : improve the exception message
                # we convert back to a standard python exception
                raise AttributeError("{sval} does not match the accepted type schema for '{s}' : {st.accepter}".format(**locals()))

        # By now the kwds is filled up with values
        # the parent init will do the usual ROS message setup.
        super(msg_mod, self).__init__(*args, **kwds)

        # registering fields in current kwds as initialized fields
        for f in optfields:
            setattr(self, f, OptionalFields(
                optional_field_names=opt_slot_list,
                optional_field_initialized_=[True if kwds.get(arg) is not None else False for arg in opt_slot_list]
            ))

        # We follow the usual ROS generated message behavior and assign our default values
        for s, st in [(_slot, typechecker_from_rosfield_type(_slot_type)) for _slot, _slot_type in zip(self.__slots__, self._slot_types)]:
            if getattr(self, s) is None:
                setattr(self, s, st.default())

    # Modifying __setattr__ to register initialization if it happens later...
    def set_opt_attr(self, attr, value):
        if attr in opt_slot_list:
            for f in get_optfields_field():
                optfields = getattr(self, f)
                if optfields and attr != f:
                    optfields.optional_field_initialized_[optfields.optional_field_names.index(attr)] = True
        super(msg_mod, self).__setattr__(attr, value)

    msg_mod.__setattr__ = set_opt_attr

    # Modifying __getattr__ to return none for an optional field if it was not explicitly set
    def get_opt_attr(self, attr):
        if attr in opt_slot_list:
            for f in get_optfields_field():
                optfields = getattr(self, f)
                if optfields and attr != f and not optfields.optional_field_initialized_[optfields.optional_field_names.index(attr)]:
                    return None  # the optional field was not set, we return None
        return super(msg_mod, self).__getattr__(attr)

    msg_mod.__getattr__ = get_opt_attr

    # duck punching into genpy generated message classes.
    msg_mod.__init__ = init_punch

    # Registering the list of optional field (required by pyros_schemas)
    msg_mod._opt_slots = opt_slot_list
