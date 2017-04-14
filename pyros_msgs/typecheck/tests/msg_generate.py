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
std_msgs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'rosdeps', 'std_msgs', 'msg')

# our own test messages we need to generate
test_gen_msg_dir = os.path.join(os.path.dirname(__file__), 'msg')


# TODO : replace this by a clever custom importer
def generate_std_msgs():
    flist = os.listdir(std_msgs_dir)
    generated_dir, generated_modules = generate_msgsrv_nspkg(
        [os.path.join(std_msgs_dir, f) for f in flist],
        package='std_msgs',
        dependencies=['std_msgs'],
        include_path=['std_msgs:{0}'.format(std_msgs_dir)],
        ns_pkg=True
    )
    assert 'std_msgs.msg' in generated_modules
    import_msgsrv('std_msgs.msg')
    std_msgs = sys.modules['std_msgs.msg']

    return std_msgs



