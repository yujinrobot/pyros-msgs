from __future__ import absolute_import, division, print_function

import copy

"""
Testing rosmsg_import with import keyword.
CAREFUL : these tests should run with pytest --boxed in order to avoid polluting each other sys.modules
"""

import os
import sys
import runpy
import logging.config

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
})

# Since test frameworks (like pytest) play with the import machinery, we cannot use it here...
import unittest

# Ref : http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path

import importlib

# Importing importer module
from pyros_msgs.importer import rosmsg_finder

# importlib
# https://pymotw.com/3/importlib/index.html
# https://pymotw.com/2/importlib/index.html


# HACK to fix spec from pytest
# @property
# def spec():
#     importlib.util.spec_from_file_location(__file__)


def print_importers():
    import sys
    import pprint

    print('PATH:'),
    pprint.pprint(sys.path)
    print()
    print('IMPORTERS:')
    for name, cache_value in sys.path_importer_cache.items():
        name = name.replace(sys.prefix, '...')
        print('%s: %r' % (name, cache_value))


class TestImportAnotherMsg(unittest.TestCase):

    rosdeps_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'rosdeps')

    @classmethod
    def setUpClass(cls):
        # We need to be before FileFinder to be able to find our '.msg' and '.srv' files without making a namespace package
        supported_loaders = rosmsg_finder._get_supported_ros_loaders()
        ros_hook = rosmsg_finder.DirectoryFinder.path_hook(*supported_loaders)
        sys.path_hooks.insert(1, ros_hook)

        sys.path.append(cls.rosdeps_path)

    @classmethod
    def tearDownClass(cls):
        # CAREFUL : Even though we remove the path from sys.path,
        # initialized finders will remain in sys.path_importer_cache
        sys.path.remove(cls.rosdeps_path)

    def test_import_absolute_pkg(self):
        print_importers()

        # Verify that files exists and are importable
        import std_msgs.msg as std_msgs

        self.assertTrue(std_msgs is not None)
        self.assertTrue(std_msgs.Bool is not None)
        self.assertTrue(callable(std_msgs.Bool))
        self.assertTrue(std_msgs.Bool._type == 'std_msgs/Bool')

    def test_import_class_from_absolute_pkg(self):
        """Verify that"""
        print_importers()

        # Verify that files exists and are importable
        from std_msgs.msg import Bool

        self.assertTrue(Bool is not None)
        self.assertTrue(callable(Bool))
        self.assertTrue(Bool._type == 'std_msgs/Bool')

    def test_import_relative_pkg(self):
        """Verify that package is importable relatively"""
        print_importers()

        from . import msg as test_msgs

        self.assertTrue(test_msgs is not None)
        self.assertTrue(test_msgs.TestMsg is not None)
        self.assertTrue(callable(test_msgs.TestMsg))
        self.assertTrue(test_msgs.TestMsg._type == 'pyros_msgs/TestMsg')  # careful between ros package name and python package name

    def test_import_class_from_relative_pkg(self):
        """Verify that message class is importable relatively"""
        print_importers()

        from .msg import TestMsg

        self.assertTrue(TestMsg is not None)
        self.assertTrue(callable(TestMsg))
        self.assertTrue(TestMsg._type == 'pyros_msgs/TestMsg')

    def test_import_class_absolute_raises(self):
        print_importers()

        with self.assertRaises(ImportError):
            import std_msgs.msg.Bool

    # TODO
    # def test_double_import_uses_cache(self):
    #     # cleaning previously imported module
    #     if 'std_msgs' in sys.modules:
    #         sys.modules.pop('std_msgs')
    #
    #     print_importers()
    #     # Verify that files exists and are importable
    #     import std_msgs.msg as std_msgs
    #
    #     self.assertTrue(std_msgs.Bool is not None)
    #     self.assertTrue(callable(std_msgs.Bool))
    #     self.assertTrue(std_msgs.Bool._type == 'std_msgs/Bool')
    #
    #     import std_msgs.msg as std_msgs2
    #
    #     self.assertTrue(std_msgs == std_msgs2)





def test_importlib_srv_module():
    pass
    # TODO
    # # Verify that files exists and are importable
    # msg_mod = importlib.import_module('test_gen_msgs.srv.TestSrv')


# imp https://pymotw.com/2/imp/index.html
# TODO

# def test_imp_msg_module():
#     # Verify that files exists and are importable
#     msg_mod = imp.import_module('test_gen_msgs.msg.TestMsg')
#
#
# def test_imp_msg_pkg():
#     # Verify that files exists and are importable
#     msg_mod = imp.import_module('test_gen_msgs.msg')
#
#
# def test_imp_srv_module():
#     # Verify that files exists and are importable
#     msg_mod = imp.import_module('test_gen_msgs.srv.TestSrv')
#
#
# def test_imp_srv_pkg():
#     # Verify that files exists and are importable
#     msg_mod = imp.import_module('test_gen_msgs.srv')


if __name__ == '__main__':
    unittest.main()
    #import nose
    #nose.main()
