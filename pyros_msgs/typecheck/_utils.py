from __future__ import absolute_import, division, print_function, unicode_literals

# PY2 Py3 ref : http://python-future.org/compatible_idioms.html

import sys
import re
import doctest


class Py32DoctestChecker(doctest.OutputChecker):

    def check_output(self, want, got, optionflags):

        # our doctests are using python3 repr. here we backport to python2
        if sys.version_info < (3, 0):
            # supporting unicode literals
            want = re.sub("u'(.*?)'", "'\\1'", want)
            want = re.sub('u"(.*?)"', '"\\1"', want)
            # supporting sets repr
            want = re.sub("{(.*?)}", "set([\\1])", want)
            # supporting type/class repr
            want = re.sub("<class '(.*?)'>", "<type '\\1'>", want)

        return doctest.OutputChecker.check_output(self, want, got, optionflags)
