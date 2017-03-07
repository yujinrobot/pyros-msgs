from __future__ import absolute_import, division, print_function

"""
TypeSchemas add extra type checking on basic python types.
Especially they add structure checks (to match ROS message types), instead of the usual python duck-typing.

This is required to detect error in a ROS message structure when it is built, instead of when it is received.
It prevents ROS message type error propagation from one node to another.

This module implement the core functionality for typeschemas, as independently as possible from implementation.
The goal here is to have a semantic representation (using python data types for simplicity) of ROS message/field types.

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

For a value V, being of any one of the types T or T' is represented by a namedtuple (sanitize=f, accept=g),
where g is defined as "lambda v : isinstance(v, (T, T'))"
Even if any types could be 'accepted', the function in the first element
will be called to convert from other accepted types into the sanitized type ST.
So f is defined as "lambda v : ST(v)"

For a value V, being an array of one type T is represented by a schema list [T]
By extension, for a value V, being an array of any one of the types T or T'
is represented by a schema list with a tuple [(T, T')]
Note [(T,)] <=> [T]

A message type is represented by a schema dict {}.
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


class TypeSchema(object):

    @staticmethod
    def accept(typeschema_accepted, *values):
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
        >>> TypeSchema.accept(bool, True)
        True
        >>> TypeSchema.accept(bool, [True])
        False
        >>> TypeSchema.accept(bool, [True, False])
        False
        >>> TypeSchema.accept([bool], True)
        False
        >>> TypeSchema.accept([bool], [False])
        True
        >>> TypeSchema.accept([bool], [False, True])
        True

        Examples with int :
        >>> TypeSchema.accept(int, 42)
        True
        >>> TypeSchema.accept([int], [42])
        True
        >>> TypeSchema.accept([(int,[int])], [[42], 23])
        True
        >>> TypeSchema.accept([six_long], six_long(42))
        False
        >>> TypeSchema.accept([int], [six_long(42)])
        False
        >>> TypeSchema.accept([(int, six_long)], [42, six_long(42)])
        True

        Examples with complex types
        >>> custom_msg = genpy.Time(23.7)
        >>> TypeSchema.accept({ 'secs': int}, custom_msg)
        True
        >>> TypeSchema.accept({ 'bad_field': int}, custom_msg)
        False
        >>> TypeSchema.accept({ 'secs': int, 'nsecs': int}, custom_msg)
        True
        >>> TypeSchema.accept({ 'secs': int, 'wrong_param': int}, custom_msg)
        False
        >>> TypeSchema.accept({ 'secs': float, 'nsecs': float}, custom_msg)
        False

        Examples with complex types and advanced predicates
        >>> custom_msg = genpy.Time(23.7)
        >>> TypeSchema.accept(lambda v : hasattr(v, 'secs') and isinstance(v.secs, int), custom_msg)
        True
        >>> TypeSchema.accept(lambda v : hasattr(v, 'bad_field') and isinstance(v.bad_field, int), custom_msg)
        False
        """

        match = False
        if isinstance(typeschema_accepted, list):  # a list denotes we also want a list, but we should check inside...
            match_all = True
            # we should have only one accepted list element type tuple
            if len(typeschema_accepted) > 1:
                raise TypeSchemaException("Error : {typeschema} has more than one element".format(**locals()))
            match_all = True
            for v in values:
                match_all = match_all and isinstance(v, list)  # make sure our value is a list
                if match_all:  # to exit early if possible
                    for ve in v:  # for all element in v
                        match_all = match_all and TypeSchema.accept(typeschema_accepted[0], ve)
            match = match_all

        elif isinstance(typeschema_accepted, dict):  # a dict denotes we also want a dict, but we should check inside...
            match_all = True
            for v in values:
                match_all = match_all and isinstance(v, (
                genpy.Time, genpy.Duration, genpy.Message))  # make sure our value is a dict or a ROS message-like object

                if match_all:  # to exit early if possible
                    for tsk, tst in typeschema_accepted.items():  # we need to match key by key
                        try:
                            match_all = match_all and TypeSchema.accept(tst, getattr(v,
                                                                          tsk))  # using getattr to be able to access slots
                        except AttributeError as ae:  # we absord the error here : it just indicates that we do not accept this value
                            match_all = False
            match = match_all

        elif isinstance(typeschema_accepted, tuple):  # a tuple denotes a set of possible types
            match_all = True
            for v in values:
                match_any = False
                for te in typeschema_accepted:
                    match_any = match_any or TypeSchema.accept(te, v)
                match_all = match_all and match_any
            match = match_all

        elif isinstance(typeschema_accepted, type):  # basic type
            match_all = True
            for v in values:
                match_all = match_all and isinstance(v, typeschema_accepted)
            match = match_all

        elif callable(typeschema_accepted):  # predicate case
            match_all = True
            for v in values:
                match = bool(typeschema_accepted(v))  # forcing predicate
                match_all = match_all and match
            match = match_all

        else:
            raise TypeSchemaException("Error : {typeschema} is not recognized".format(**locals()))

        return match

    @staticmethod
    def sanitize(typeschema_sanitized, value):
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

        >>> TypeSchema.sanitize(bool, True)
        True
        >>> TypeSchema.sanitize(int, 42)
        42
        >>> TypeSchema.sanitize([int], 42)
        [42]
        >>> TypeSchema.sanitize(int, [42])
        Traceback (most recent call last):
        ...
        TypeError: int() argument must be a string or a number, not 'list'
        >>> TypeSchema.sanitize([int], [42])
        [42]
        >>> TypeSchema.sanitize(six_long, 42)
        42L
        >>> TypeSchema.sanitize(int, 42L)
        42

        Examples with complex types
        >>> custom_msg = genpy.Time(23.7)
        >>> TypeSchema.sanitize(lambda v: genpy.Duration(secs=v.secs), custom_msg)
        genpy.Duration[23000000000]
        >>> TypeSchema.sanitize(lambda v: genpy.Duration(secs=v.secs, nsecs=v.nsecs), custom_msg)
        genpy.Duration[23699999999]

        """

        # we get the first element of the tuple directly (sanitized type)
        # if isinstance(typeschema_sanitized, tuple):
        #     typeschema_sanitized = typeschema_sanitized[0]

        if isinstance(typeschema_sanitized, list):  # a list denotes we also generate a list, but we should check inside...
            # we should have only one accepted list element type tuple
            if len(typeschema_sanitized) > 1:
                raise TypeSchemaException("Error : {typeschema} has more than one element".format(**locals()))
            value = [TypeSchema.sanitize(typeschema_sanitized[0], v) for v in maybe_list(value)]
        # elif isinstance(typeschema_sanitized, dict):  # a dict denotes we expect an message object, and we should extract slots.
        #     if '_sanitized' not in typeschema_sanitized:
        #         raise TypeSchemaException("'_sanitized' has to be a key in {generated_typeschema}".format(**locals()))
        #     # however slots are sometimes not available
        #     # like rospy.Time which has no slots but is inheriting from genpy.Time which has...
        #     # => we use filtering to retrieve the members we are interested in.
        #     value = TypeSchema.sanitize(typeschema_sanitized['_sanitized'],
        #                      {vk: TypeSchema.sanitize(typeschema_sanitized[vk], getattr(value, vk)) for vk in typeschema_sanitized if vk != '_sanitized'})
        else:  # basic type
            # # if we have a dict we can pass multiple arguments to a composed type constructor
            # if isinstance(value, dict):
            #     value = typeschema_sanitized(**value)
            # else:
            value = typeschema_sanitized(value)

        return value

    def __init__(self, sanitized_type, accepted_types):
        """
        :param sanitized_type: the representation of the type to sanitize to.
                    Can contain :
                        - basic type
                        - list of one basic type
                        - dict of keywords and types.
                    The first element of any tuple will be generated.
        :param accepted_types: the representation of accepted types.
                    Can contain :
                        - basic type
                        - tuple of basic types
                        - list of one basic type or a tuple
                        - dict of keywords and types.
                    All element of any tuple will be accepted.
        """

        self.sanitized_type = sanitized_type

        if isinstance(sanitized_type, list):  # a list denotes we also want a list, but we should check inside...
            # we should have only one sanitize list element type tuple
            if len(sanitized_type) > 1:
                raise TypeSchemaException("Error : {sanitized_type} has more than one element".format(**locals()))

            pass

        elif isinstance(sanitized_type,
                        dict):  # a dict denotes we also want a specific set of fields, but we should check inside...
            pass

        elif isinstance(sanitized_type, tuple):
            # we should have only one sanitize element type tuple
            if len(sanitized_type) > 1:
                raise TypeSchemaException("Error : {sanitized_type} has more than one element".format(**locals()))

        else:  # basic type
            pass

        self.sanitized_type = sanitized_type

        if isinstance(accepted_types, list):  # a list denotes we also want a list, but we should check inside...
            # we should have only one accepted list element type tuple
            if len(self.accepted_types) > 1:
                raise TypeSchemaException("Error : {typeschema} has more than one element".format(**locals()))
            pass

        elif isinstance(accepted_types,
                        dict):  # a dict denotes we also want a specific set of fields, but we should check inside...
            pass

        elif isinstance(accepted_types, tuple):  # a tuple denotes a set of possible types
            pass

        else:  # basic type
            pass

        self.accepted_types = accepted_types

    def __call__(self, value):
        """

        :param value:
        :param typeschema:
        :return:
        """

        if TypeSchema.accept(self.accepted_types, value):
            sanitized_value = TypeSchema.sanitize(self.sanitized_type, value)
        else:
            raise TypeSchemaException("value '{value}' does not match the type schema {self.accepted_types}".format(**locals()))

        return sanitized_value

    def __repr__(self):
        return "({self.sanitized_type}, {self.accepted_types})".format(**locals())


    def default(self):
        """
        Retrieves a default value based on the typeschema
        :param typeschema: the type schema
        :return: default value for that type

        >>> bool_ts = TypeSchema(bool, bool)
        >>> bool_ts.default()
        False

        >>> int_ts = TypeSchema(int, int)
        >>> int_ts.default()
        0

        >>> float_ts = TypeSchema(float, float)
        >>> float_ts.default()
        0.0

        >>> str_ts = TypeSchema(str, str)
        >>> str_ts.default()
        ''

        >>> array_ts = TypeSchema([bool], [bool])
        >>> array_ts.default()
        []
        >>> array_ts = TypeSchema([int], [int])
        >>> array_ts.default()
        []
        >>> array_ts = TypeSchema([float], [float])
        >>> array_ts.default()
        []
        >>> array_ts = TypeSchema([str], [str])
        >>> array_ts.default()
        []
        >>> array_ts = TypeSchema([float], [float])
        >>> array_ts.default()
        []

        >>> time_ts = TypeSchema(genpy.Time, genpy.Time)
        >>> time_ts.default()
        genpy.Time[0]

        >>> duration_ts = TypeSchema(genpy.Duration, genpy.Duration)
        >>> duration_ts.default()
        genpy.Duration[0]

        """

        if isinstance(self.sanitized_type, list):  # a list denotes we also generate a list, but we should check inside...
            # we should have only one accepted list element type tuple
            if len(self.sanitized_type) > 1:
                raise TypeSchemaException("Error : {typeschema} has more than one element".format(**locals()))
            def_value = []
        # elif isinstance(self.sanitized_type, dict):  # a dict denotes we expect an message object, and we should extract slots.
        #     def_value = typeschema_default(self.sanitized_type['_sanitized'])
        else:  # basic type
            # note we let the type default implementation deal with it.
            # works for basic type or message types
            def_value = self.sanitized_type()

        return def_value

