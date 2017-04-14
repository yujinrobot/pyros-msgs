from __future__ import absolute_import, division, print_function

import os
import sys

"""
module handling test message generation and import.
We need to generate all and import only one time ( in case we have one instance of pytest running multiple tests )
"""

from pyros_msgs.importer.rosmsg_generator import generate_msgsrv_nspkg, import_msgsrv

# These depends on file structure and should no be in functions

# dependencies for our generated messages
pyros_msgs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'msg')

# our own test messages we need to generate
test_gen_msg_dir = os.path.join(os.path.dirname(__file__), 'msg')


# TODO : replace this by a clever custom importer
def generate_pyros_msgs():
    flist = os.listdir(pyros_msgs_dir)
    generated_dir, generated_modules = generate_msgsrv_nspkg(
        [os.path.join(pyros_msgs_dir, f) for f in flist],
        package='pyros_msgs',
        ns_pkg=True
    )
    assert 'pyros_msgs.msg' in generated_modules
    import_msgsrv('pyros_msgs.msg')
    pyros_msgs = sys.modules['pyros_msgs.msg']

    return pyros_msgs


def generate_test_msgs():
    try:
        # This should succeed if the message has been generated previously (or accessing ROS generated message)
        import pyros_msgs.msg as pyros_msgs
    except ImportError:  # we should enter here if the message class hasnt been generated yet.
        pyros_msgs = generate_pyros_msgs()

    flist = os.listdir(test_gen_msg_dir)
    generated_dir, generated_modules = generate_msgsrv_nspkg(
        [os.path.join(test_gen_msg_dir, f) for f in flist],
        package='test_nested_gen_msgs',
        dependencies=['pyros_msgs'],
        include_path=['pyros_msgs:{0}'.format(pyros_msgs_dir)],
        ns_pkg=True
    )
    assert 'test_nested_gen_msgs.msg' in generated_modules
    import_msgsrv('test_nested_gen_msgs.msg')
    test_gen_msgs = sys.modules['test_nested_gen_msgs.msg']

    return test_gen_msgs


