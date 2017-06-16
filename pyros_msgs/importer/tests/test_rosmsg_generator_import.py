from __future__ import absolute_import, division, print_function

import importlib

"""
Testing executing rosmsg_generator directly (like setup.py would)
"""

import os
import runpy

# Ref : http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path

# Importing importer module
from pyros_msgs.importer import rosmsg_importer


def setup_module():
    rosmsg_importer.activate()


def teardown_module():
    rosmsg_importer.deactivate()


# importlib
# https://pymotw.com/3/importlib/index.html
# https://pymotw.com/2/importlib/index.html

def test_importlib_msg_module_absolute():
    # Verify that files exists and are importable
    if hasattr(importlib, 'find_loader'):  # recent version of import lib

        pkg_loader = importlib.find_loader('test_gen_msgs')
        pkg = pkg_loader.load_module()

        subpkg_loader = importlib.find_loader('msg', pkg.__path__)
        subpkg = subpkg_loader.load_module()

        loader = importlib.find_loader('TestMsg', subpkg.__path__)
        msg_mod = subpkg_loader.load_module()

    else:  # old version
        msg_mod = importlib.import_module('pyros_msgs.importer.tests.msg.TestMsg')

    if hasattr(importlib, 'reload'):  # recent version of importlib
        # attempting to reload
        importlib.reload(msg_mod)
    else:
        pass



# def test_importlib_msg_module_relative():
#     # Verify that files exists and are importable
#     # TODO
#     # if hasattr(importlib, 'find_loader'):  # recent version of import lib
#     #
#     #     pkg_loader = importlib.find_loader('test_gen_msgs')
#     #     pkg = pkg_loader.load_module()
#     #
#     #     subpkg_loader = importlib.find_loader('msg', pkg.__path__)
#     #     subpkg = subpkg_loader.load_module()
#     #
#     #     loader = importlib.find_loader('TestMsg', subpkg.__path__)
#     #     m = subpkg_loader.load_module()
#     #
#     # else:  # old version
#     msg_mod = importlib.import_module('.msg.TestMsg', package=__package__)




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


# TODO : different python versions...

