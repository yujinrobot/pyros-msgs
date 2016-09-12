from __future__ import absolute_import
from __future__ import print_function

import sys
import doctest

import nose


# duplicating here because nose wont make difference between multiple tests names from a generator
# Anyway it's simple enough.

def test_schema_std_Empty_doctest():
    for t in doctest.DocTestSuite("pyros_msgs.schema.std_Empty"):
        yield t


def test_schema_std_Bool_doctest():
    for t in doctest.DocTestSuite("pyros_msgs.schema.std_Bool"):
        yield t


def test_schema_std_Int_doctest():
    for t in doctest.DocTestSuite("pyros_msgs.schema.std_Int"):
        yield t


def test_schema_std_Float_doctest():
    for t in doctest.DocTestSuite("pyros_msgs.schema.std_Float"):
        yield t


def test_schema_std_String_doctest():
    for t in doctest.DocTestSuite("pyros_msgs.schema.std_String"):
        yield t


def test_schema_std_Time_doctest():
    for t in doctest.DocTestSuite("pyros_msgs.schema.std_Time"):
        yield t


def test_schema_std_Duration_doctest():
    for t in doctest.DocTestSuite("pyros_msgs.schema.std_Duration"):
        yield t


def test_schema_std_Header_doctest():
    for t in doctest.DocTestSuite("pyros_msgs.schema.std_Header"):
        yield t


# Just in case we run this directly
if __name__ == '__main__':
    nose.runmodule(__name__)
