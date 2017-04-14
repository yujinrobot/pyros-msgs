from __future__ import absolute_import, division, print_function

"""
Testing executing rosmsg_generator directly (like setup.py would)
"""

import os
import runpy

# Ref : http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path

# Including generator module directly from code to be able to generate our message classes
import imp
rosmsg_generator = imp.load_source('rosmsg_generator', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'rosmsg_generator.py'))


def test_generate_msgsrv_nspkg_usable():
    # generating message class
    generated_dir, generated_modules = rosmsg_generator.generate_msgsrv_nspkg(
        [os.path.join(os.path.dirname(__file__), 'msg', 'TestMsg.msg')],
        package='test_gen_msgs',
        initpy=True,
    )

    for m in generated_modules:
        # modules are generated where the file is launched
        gen_file = os.path.join(os.getcwd(), *m.split("."))
        assert os.path.exists(gen_file + '.py') or os.path.exists(os.path.join(gen_file, '__init__.py'))


