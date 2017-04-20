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
std_msgs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'rosdeps', 'std_msgs', 'msg')


# our own test messages we need to generate
test_gen_msg_dir = os.path.join(os.path.dirname(__file__), 'msg')



# TODO : replace this by a clever custom importer
def generate_pyros_msgs():
    flist = os.listdir(pyros_msgs_dir)
    #flist = flist + os.listdir(std_msgs_dir)
    generated = generate_msgsrv_nspkg(
        [os.path.join(pyros_msgs_dir, f) for f in flist],
        package='pyros_msgs',
        dependencies=['pyros_msgs'],
        include_path=['pyros_msgs:{0}'.format(pyros_msgs_dir)],
        ns_pkg=True
    )
    pyros_msgs_msg, pyros_srvs_srv = import_msgsrv(*generated)

    return pyros_msgs_msg, pyros_srvs_srv

def generate_std_msgs():
    flist = os.listdir(std_msgs_dir)
    generated = generate_msgsrv_nspkg(
        [os.path.join(std_msgs_dir, f) for f in flist],
        package='std_msgs',
        dependencies=['std_msgs'],
        include_path=['std_msgs:{0}'.format(std_msgs_dir)],
        ns_pkg=True
    )
    std_msgs, std_srvs = import_msgsrv(*generated)

    return std_msgs, std_srvs


def generate_test_msgs():
    try:
        # This should succeed if the message has been generated previously (or accessing ROS generated message)
        import pyros_msgs.msg as pyros_msgs
    except ImportError:  # we should enter here if the message class hasn't been generated yet.
        pyros_msgs_msg, pyros_msgs_srv = generate_pyros_msgs()

    try:
        # This should succeed if the message class was already generated
        import std_msgs.msg as std_msgs
    except ImportError:  # we should enter here if the message was not generated yet.
        _, _ = generate_std_msgs()

    flist = os.listdir(test_gen_msg_dir)
    #flist = flist + os.listdir(std_msgs_dir)
    generated = generate_msgsrv_nspkg(
        [os.path.join(test_gen_msg_dir, f) for f in flist],
        package='test_nested_gen_msgs',
        dependencies=['pyros_msgs', 'std_msgs'],
        include_path=['pyros_msgs:{0}'.format(pyros_msgs_dir), 'std_msgs:{0}'.format(std_msgs_dir)],
        ns_pkg=True
    )
    test_gen_msgs, test_gen_srvs = import_msgsrv(*generated)

    return test_gen_msgs, test_gen_srvs




