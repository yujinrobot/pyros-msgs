from __future__ import absolute_import, division, print_function

import functools

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


def maybe_list(l):
    """Return list of one element if ``l`` is a scalar."""
    return l if l is None or isinstance(l, list) else [l]


def maybe_tuple(t):
    """Return tuple of one element if ``t`` is a scalar."""
    return t if t is None or isinstance(t, tuple) else (t,)


def maybe_set(t):
    """Return tuple of one element if ``t`` is a scalar."""
    return t if t is None or isinstance(t, set) else {t}

#
# SANITIZERS for field types
# Used to construct a new default value or to modify a value passed as argument
#


# Using classes and object hierarchy to represent sanitizer and accepter functions since python prefers that
class Sanitizer(object):
    def __init__(self, t):
        self.t = t

    def __call__(self, *args, **kwargs):
        # we sanitize by running the type initializer with the value
        return self.t(*args, **kwargs)

    def __repr__(self):
        return "Sanitizer to {self.t}".format(**locals())

#
# ACCEPTERS for field types
# Used to certify the type match (duck typing for composed types)
#


class Accepter(object):
    def __init__(self, t):
        self.t = t

    def __call__(self, v):
        if isinstance(self.t, dict):
            return all(hasattr(v, s) and self.t.get(s).accepter(getattr(v, s)) for s, st in self.t.items())
        else:  # basic type
            return isinstance(v, self.t)

    def __repr__(self):
        return "Accepter from {self.t}".format(**locals())


#
# Operators on Sanitizer or Accepter
#

class Any(object):
    def __init__(self, *at):
        assert all(isinstance(aet, (Accepter, Array)) for aet in at)  # Note Any makes sense only for Accepter
        self.at = at

    def __call__(self, v):
        return any(st(v) for st in self.at)

    def __repr__(self):
        return "Any of {self.at}".format(**locals())


class Array(object):
    def __init__(self, t):
        """
        Array can be used with both sanitizer or accepter.
        It has different meaning for each
        :param t: the sanitizer or accepter to use for each element
        """
        assert isinstance(t, (Sanitizer, Accepter, Any, Array))
        self.t = t  # only the first element of that list is valid

    def __call__(self, v=None):
        if isinstance(self.t, (Sanitizer)):
            # Array mean generate an array
            return [self.t(e) for e in v] if v is not None else []
        elif isinstance(self.t, (Accepter, Any)):
            # Array mean check all elements
            return all(self.t(e) for e in v)
        else:  # should never happen
            raise TypeCheckerException("function for Array is neither a Sanitizer or an Accepter")

    def __repr__(self):
        return "Array of {self.t}".format(**locals())


class TypeCheckerException(Exception):
    pass


class TypeChecker(object):
    def __init__(self, sanitizer, accepter):
        """
        :param sanitizer: a function to be used as sanitizer
        :param accepter: a function to be used as accepter
        """

        self.sanitizer = sanitizer
        self.accepter = accepter

    def __call__(self, value):
        """
        TypeCheck (with accepter) and sanitize (with sanitizer) the value.
        Returns an exception if the value cannot be accepted.
        Sanitizer may also return an exception if conversion is not possible.
        :param value: the value to typecheck
        :return: sanitized value

        Examples with bool and bool array :
        >>> bool_tc = TypeChecker(Sanitizer(bool), Accepter(bool))
        >>> bool_tc(True)
        True
        >>> bool_tc([True])
        Traceback (most recent call last):
        ...
        TypeCheckerException: '[True]:<type 'list'>' is not accepted by Accepter from <type 'bool'>
        >>> bool_tc([True, False])
        Traceback (most recent call last):
        ...
        TypeCheckerException: '[True, False]:<type 'list'>' is not accepted by Accepter from <type 'bool'>
        >>> boolarray_tc = TypeChecker(Array(Sanitizer(bool)), Array(Accepter(bool)))
        >>> boolarray_tc(True)
        Traceback (most recent call last):
        ...
        TypeCheckerException: 'True:<type 'bool'>' cannot be accepted by Array of Accepter from <type 'bool'>
                      Reason: 'bool' object is not iterable
        >>> boolarray_tc([False])
        [False]
        >>> boolarray_tc([False, True])
        [False, True]

        Examples with int :
        >>> int_tc = TypeChecker(Sanitizer(int), Accepter(int))
        >>> int_tc(42)
        42
        >>> intarray_tc = TypeChecker(Array(Sanitizer(int)), Array(Accepter(int)))
        >>> intarray_tc([42])
        [42]
        >>> intoptarray_array_tc = TypeChecker(Array(Sanitizer(int)), Array(Any(Accepter(int), Array(Accepter(int)))))
        >>> intoptarray_array_tc([[42], 23])
        Traceback (most recent call last):
        ...
        TypeCheckerException: '[[42], 23]:<type 'list'> cannot be sanitized by Array of Sanitizer to <type 'int'>
                      Reason: int() argument must be a string or a number, not 'list'
        >>> longarray_tc = TypeChecker(Array(Sanitizer(six_long)), Array(Accepter(six_long)))
        >>> longarray_tc(six_long(42))
        Traceback (most recent call last):
        ...
        TypeCheckerException: '42:<type 'long'>' cannot be accepted by Array of Accepter from <type 'long'>
                      Reason: 'long' object is not iterable
        >>> intarray_tc = TypeChecker(Array(Sanitizer(int)), Array(Accepter(int)))
        >>> intarray_tc([six_long(42)])
        Traceback (most recent call last):
        ...
        TypeCheckerException: '[42L]:<type 'list'>' is not accepted by Array of Accepter from <type 'int'>
        >>> intlongarray = TypeChecker(Array(Sanitizer(six_long)), Array(Any(Accepter(int), Accepter(six_long))))
        >>> intlongarray([42, six_long(42)])
        [42L, 42L]

        Examples with complex types
        >>> class Custom(object):
        ...     def __init__(self, d1=0, d2=''):
        ...         self.d1 = d1; self.d2 = d2
        ...     def __repr__(self):
        ...         return "d1:{d1} d2:{d2}".format(d1=self.d1, d2=self.d2)
        >>> custom_msg = Custom(42, d2='bla')

        with a simple sanitizing function
        >>> customd1_sanitizer = lambda x=None: Custom(d1=x.d1) if x else Custom()
        >>> customd1_tc = TypeChecker(Sanitizer(customd1_sanitizer), Accepter({
        ...     'd1': TypeChecker(Sanitizer(int), Accepter(int))
        ... }))
        >>> customd1_tc(custom_msg)
        d1:42 d2:

        we can filter some members on the sanitizing function
        >>> customd1d2_sanitizer = lambda x=None: Custom(d1=x.d1, d2=x.d2) if x else Custom()
        >>> customd1d2_tc = TypeChecker(Sanitizer(customd1d2_sanitizer), Accepter({
        ...     'd1': TypeChecker(Sanitizer(int),Accepter(int)),
        ...     'd2': TypeChecker(Sanitizer(str), Any(Accepter(str), Accepter(unicode)))
        ... }))
        >>> customd1d2_tc(custom_msg)
        d1:42 d2:bla

        >>> customd1d2_tc = TypeChecker(Sanitizer(customd1d2_sanitizer), Accepter({
        ...     'd1': TypeChecker(Sanitizer(int),Accepter(int)),
        ...     'bad_field': TypeChecker(Sanitizer(int),Accepter(int))
        ... }))
        >>> customd1d2_tc(custom_msg)
        Traceback (most recent call last):
        ...
        TypeCheckerException: 'd1:42 d2:bla:<class 'typechecker.Custom'>' is not accepted by Accepter from {'bad_field': (Sanitizer to <type 'int'>, Accepter from <type 'int'>), 'd1': (Sanitizer to <type 'int'>, Accepter from <type 'int'>)}

        >>> customd1d2_tc = TypeChecker(Sanitizer(customd1d2_sanitizer), Accepter({
        ...     'd1': TypeChecker(Sanitizer(int),Accepter(int)),
        ...     'd2': TypeChecker(Sanitizer(int),Accepter(int))
        ... }))
        >>> customd1d2_tc(custom_msg)
        Traceback (most recent call last):
        ...
        TypeCheckerException: 'd1:42 d2:bla:<class 'typechecker.Custom'>' is not accepted by Accepter from {'d2': (Sanitizer to <type 'int'>, Accepter from <type 'int'>), 'd1': (Sanitizer to <type 'int'>, Accepter from <type 'int'>)}
        """
        try:
            accepted = self.accepter(value)
        except Exception as e:
            raise TypeCheckerException("'{v}:{vt}' cannot be accepted by {a}\n              Reason: {e}".format(
                v=value, vt=type(value), a=self.accepter, e=e
            ))

        if accepted:
            try:
                sanitized_value = self.sanitizer(value)
            except TypeError as te:
                raise TypeCheckerException("'{v}:{vt} cannot be sanitized by {s}\n              Reason: {te}".format(
                    v=value, vt=type(value), s=self.sanitizer, te=te
                ))
        else:
            raise TypeCheckerException("'{v}:{vt}' is not accepted by {a}".format(
                v=value, vt=type(value), a=self.accepter
            ))

        return sanitized_value

    def __repr__(self):
        return "({self.sanitizer}, {self.accepter})".format(**locals())

    def default(self):
        """
        Retrieves a default value based on the typeschema
        :param typeschema: the type schema
        :return: default value for that type

        Examples:
        >>> bool_ts = TypeChecker(Sanitizer(bool), Accepter(bool))
        >>> bool_ts.default()
        False

        >>> int_ts = TypeChecker(Sanitizer(int), Accepter(int))
        >>> int_ts.default()
        0

        >>> float_ts = TypeChecker(Sanitizer(float), Accepter(float))
        >>> float_ts.default()
        0.0

        >>> str_ts = TypeChecker(Sanitizer(str), Accepter(str))
        >>> str_ts.default()
        ''

        >>> array_ts = TypeChecker(Array(Sanitizer(bool)), Array(Accepter(bool)))
        >>> array_ts.default()
        []
        >>> array_ts = TypeChecker(Array(Sanitizer(int)), Array(Accepter(int)))
        >>> array_ts.default()
        []
        >>> array_ts = TypeChecker(Array(Sanitizer(float)), Array(Accepter(float)))
        >>> array_ts.default()
        []
        >>> array_ts = TypeChecker(Array(Sanitizer(str)), Array(Accepter(str)))
        >>> array_ts.default()
        []
        >>> array_ts = TypeChecker(Array(Sanitizer(float)), Array(Accepter(float)))
        >>> array_ts.default()
        []


        Examples with complex types
        >>> class Custom(object):
        ...     def __init__(self, d1=0, d2=''):
        ...         self.d1 = d1; self.d2 = d2
        ...     def __repr__(self):
        ...         return "d1:{d1} d2:{d2}".format(d1=self.d1, d2=self.d2)
        >>> custom_msg = Custom(42, d2='bla')

        >>> customd1_sanitizer = lambda x=None: Custom(d1=x.d1) if x else Custom(d1=1)
        >>> customd1_tc = TypeChecker(Sanitizer(customd1_sanitizer), Accepter({
        ...     'd1': TypeChecker(Sanitizer(int), Accepter(int))
        ... }))
        >>> customd1_tc.default()
        d1:1 d2:


        """
        return self.sanitizer()


