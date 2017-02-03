#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import sys
import utool as ut

if __name__ == '__main__':
    import vtool.tests.run_tests
    import multiprocessing
    ut.change_term_title('RUN VTOOL TESTS')
    multiprocessing.freeze_support()
    retcode = vtool.tests.run_tests.run_tests()
    sys.exit(retcode)
