from __future__ import absolute_import, division, print_function

"""
TypeSchemas add extra type checking on basic python types.
Especially they add structure checks (to match ROS message types), instead of the usual python duck-typing.

This is required to detect error in a ROS message structure when it is built, instead of when it is received.
It prevents ROS message type error propagation from one node to another.

This module implement the core functionality for typeschemas, as independently as possible from implementation.

For ease of implementation, and despite the potential confusion, type schemas will be implemented with python types

In a ROS message, a field can have a value of one of the basic types :
- bool,
- int, (careful with long and python2)
- float,
- string, (careful with unicode and python2)
- time,
- duration

or of a composed type T :
- array/list
- another message type ( = dict of fields' types )

For a value V, being of any one of the types T or T' is represented by a schema tuple (T, T').
Note the first type of that tuple will be the type 'sanitized' for that value.
Even if all types could be 'accepted', the constructor of the first type
will be used to convert from other accepted types into the 'sanitized' type

For a value V, being an array of one type T is represented by a schema list [T]
By extension, for a value V, being an array of any one of the types T or T'
is represented by a schema list with a tuple [(T, T')]
Note [(T,)] <=> [T]

A message type is represented by a schema dict {}.
The dict contains a special key '_sanitized', indicating which type must be generated from the accepted types
The keys denote the message fields names, and the values are the types, following the previous rules.
"""


import six
# to get long for py2 and int for py3
six_long = six.integer_types[-1]


try:
    import genpy
except ImportError:
    import pyros_setup
    pyros_setup.configurable_import().configure().activate()
    import genpy


def maybe_list(l):
    """Return list of one element if ``l`` is a scalar."""
    return l if l is None or isinstance(l, list) else [l]


def maybe_tuple(t):
    """Return tuple of one element if ``t`` is a scalar."""
    return t if t is None or isinstance(t, tuple) else (t,)

#
# def maybe_dict(t):
#     """Return dict of one element if ``t`` is a scalar."""
#     return t if t is None or isinstance(t, dict) else {'data': t}


class TypeSchemaException(Exception):
    pass


def accept(typeschema, *values):
    """
    Determining if a value matches any of the type in the accepted_type_tuple
    :param typeschema: the typeschema of accepted types. Can contain :
                        - basic type
                        - tuple of basic types
                        - list of one basic type or a tuple
                        - dict of keywords and types.
                    All element of any tuple will be accepted.
    :param args: multiple values to check if they match the typeschema
    :return: True if all the value are acceptable, False otherwise

    Examples with bool :
    >>> accept(bool, True)
    True
    >>> accept(bool, [True])
    False
    >>> accept(bool, [True, False])
    False
    >>> accept([bool], True)
    False
    >>> accept([bool], [False])
    True
    >>> accept([bool], [False, True])
    True

    Examples with int :
    >>> accept(int, 42)
    True
    >>> accept([int], [42])
    True
    >>> accept([(int,[int])], [[42], 23])
    True
    >>> accept([six_long], six_long(42))
    False
    >>> accept([int], [six_long(42)])
    False
    >>> accept([(int, six_long)], [42, six_long(42)])
    True

    Examples with composed types
    >>> custom_msg = genpy.Time(23.7)
    >>> accept({ 'secs': int}, custom_msg)
    True
    >>> accept({ 'bad_field': int}, custom_msg)
    False
    >>> accept({ 'secs': int, 'nsecs': int}, custom_msg)
    True
    >>> accept({ 'secs': int, 'wrong_param': int}, custom_msg)
    False
    >>> accept({ 'secs': float, 'nsecs': float}, custom_msg)
    False
    """
    match = False
    if isinstance(typeschema, list):  # a list denotes we also want a list, but we should check inside...
        match_all = True
        # we should have only one accepted list element type tuple
        if len(typeschema) > 1:
            raise TypeSchemaException("Error : {typeschema} has more than one element".format(**locals()))
        match_all = True
        for v in values:
            match_all = match_all and isinstance(v, list)  # make sure our value is a list
            if match_all:  # to exit early if possible
                for ve in v:  # for all element in v
                    match_all = match_all and accept(typeschema[0], ve)
        match = match_all

    elif isinstance(typeschema, dict):  # a dict denotes we also want a dict, but we should check inside...
        match_all = True
        for v in values:
            match_all = match_all and isinstance(v, (genpy.Time, genpy.Duration, genpy.Message))  # make sure our value is a dict or a ROS message-like object

            if match_all:  # to exit early if possible
                for tsk, tst in typeschema.items():  # we need to match key by key
                    if tsk != '_sanitized':
                        try:
                            match_all = match_all and accept(tst, getattr(v, tsk)) # using getattr to be able to access slots
                        except AttributeError as ae:  # we absord the error here : it just indicates that we do not accept this value
                            match_all = False
        match = match_all

    elif isinstance(typeschema, tuple):  # a tuple denotes a set of possible types
        match_all = True
        for v in values:
            match_any = False
            for te in typeschema:
                match_any = match_any or accept(te, v)
            match_all = match_all and match_any
        match = match_all

    else:  # basic type
        match_all = True
        for v in values:
            match_all = match_all and isinstance(v, typeschema)
        match = match_all
    return match


def sanitize(typeschema, value):
    """
    Converting a value to match the generated_type
    :param typeschema: the typeschema to sanitize to. Can contain :
                        - basic type
                        - tuple of basic types
                        - list of one basic type or a tuple
                        - dict of keywords and types.
                    The first element of any tuple will be generated.
    :param value: the value to sanitize
    :return: Sanitized value

    >>> sanitize(bool, True)
    True
    >>> sanitize(int, 42)
    42
    >>> sanitize([int], 42)
    [42]
    >>> sanitize(int, [42])
    Traceback (most recent call last):
    ...
    TypeError: int() argument must be a string or a number, not 'list'
    >>> sanitize([int], [42])
    [42]
    >>> sanitize(six_long, 42)
    42L
    >>> sanitize(int, 42L)
    42

    Examples with composed types
    >>> custom_msg = genpy.Time(23.7)
    >>> sanitize({ '_sanitized': genpy.Duration, 'secs': int}, custom_msg)
    genpy.Duration[23000000000]
    >>> sanitize({ '_sanitized': genpy.Duration, 'secs': int, 'nsecs': int}, custom_msg)
    genpy.Duration[23699999999]

    """

    # we get the first element of the tuple directly (sanitized type)
    if isinstance(typeschema, tuple):
        typeschema = typeschema[0]

    if isinstance(typeschema, list):  # a list denotes we also generate a list, but we should check inside...
        # we should have only one accepted list element type tuple
        if len(typeschema) > 1:
            raise TypeSchemaException("Error : {typeschema} has more than one element".format(**locals()))
        value = [sanitize(typeschema[0], v) for v in maybe_list(value)]
    elif isinstance(typeschema, dict):  # a dict denotes we expect an message object, and we should extract slots.
        if '_sanitized' not in typeschema:
            raise TypeSchemaException("'_sanitized' has to be a key in {generated_typeschema}".format(**locals()))
        # however slots are sometimes not available
        # like rospy.Time which has no slots but is inheriting from genpy.Time which has...
        # => we use filtering to retrieve the members we are interested in.
        value = sanitize(typeschema['_sanitized'], {vk: sanitize(typeschema[vk], getattr(value, vk)) for vk in typeschema if vk != '_sanitized'})
    else:  # basic type
        # if we have a dict we can pass multiple arguments to a composed type constructor
        if isinstance(value, dict):
            value = typeschema(**value)
        else:
            value = typeschema(value)

    return value


def typeschema_check(typeschema, value):
    """

    :param value:
    :param typeschema:
    :return:
    """

    if accept(typeschema, value):
        sanitized_value = sanitize(typeschema, value)
    else:
        raise TypeSchemaException("value '{value}' does not match the type schema {typeschema}".format(**locals()))

    return sanitized_value


def typeschema_default(typeschema):
    """
    Retrieves a default value based on the typeschema
    :param typeschema: the type schema
    :return: default value for that type

    >>> typeschema_default(bool)
    False

    >>> typeschema_default(int)
    0

    >>> typeschema_default(float)
    0.0

    >>> typeschema_default(str)
    ''

    >>> typeschema_default([bool])
    []
    >>> typeschema_default([int])
    []
    >>> typeschema_default([float])
    []
    >>> typeschema_default([str])
    []
    >>> typeschema_default([float])
    []

    >>> typeschema_default(genpy.Time)
    genpy.Time[0]

    >>> typeschema_default(genpy.Duration)
    genpy.Duration[0]

    """
    # we get the first element of the tuple directly (sanitized type)
    if isinstance(typeschema, tuple):
        typeschema = typeschema[0]

    if isinstance(typeschema, list):  # a list denotes we also generate a list, but we should check inside...
        # we should have only one accepted list element type tuple
        if len(typeschema) > 1:
            raise TypeSchemaException("Error : {typeschema} has more than one element".format(**locals()))
        def_value = []
    elif isinstance(typeschema, dict):  # a dict denotes we expect an message object, and we should extract slots.
        if '_sanitized' not in typeschema:
            raise TypeSchemaException("'_sanitized' has to be a key in {generated_typeschema}".format(**locals()))
        def_value = typeschema_default(typeschema['_sanitized'])
    else:  # basic type
        # note we let the type default implementation deal with it.
        # works for basic type or message types
        def_value = typeschema()

    return def_value

