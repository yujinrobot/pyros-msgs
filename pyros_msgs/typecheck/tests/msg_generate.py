from __future__ import absolute_import, division, print_function

import os
import sys

"""
module handling test message generation and import.
We need to generate all and import only one time ( in case we have one instance of pytest running multiple tests )
"""

# These depends on file structure and should no be in functions

# dependencies for our generated messages
rosdeps_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'rosdeps')

# our own test messages we need to generate
test_gen_msg_dir = os.path.join(os.path.dirname(__file__), 'msg')

import rosimport
rosimport.activate()


# # TODO : replace this by a clever custom importer
# def generate_std_msgs():
#     flist = os.listdir(std_msgs_dir)
#     generated = generate_msgsrv_nspkg(
#         [os.path.join(std_msgs_dir, f) for f in flist],
#         package='std_msgs',
#         dependencies=['std_msgs'],
#         include_path=['std_msgs:{0}'.format(std_msgs_dir)],
#         ns_pkg=True
#     )
#     test_gen_msgs, test_gen_srvs = import_msgsrv(*generated)
#
#     return test_gen_msgs, test_gen_srvs



