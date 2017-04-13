from __future__ import absolute_import, division, print_function

import os
import sys

"""
module handling test message generation and import.
We need to generate all and import only one time ( in case we have one instance of pytest running multiple tests )
"""

from pyros_msgs.importer.rosmsg_generator import generate_msgsrv_nspkg, import_msgsrv


def generate_test_msgs():
    std_msgs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'rosdeps', 'std_msgs', 'msg')
    test_gen_msg_dir = os.path.join(os.path.dirname(__file__), 'msg')
    flist = os.listdir(test_gen_msg_dir)
    generated_modules = generate_msgsrv_nspkg(
        [os.path.join(test_gen_msg_dir, f) for f in flist],
        package='test_gen_msgs',
        dependencies=['std_msgs'],
        include_path=['std_msgs:{0}'.format(std_msgs_dir)],
       ns_pkg=True
    )
    import_msgsrv('test_gen_msgs.msg')
    test_gen_msgs = sys.modules['test_gen_msgs.msg']

    return test_gen_msgs

