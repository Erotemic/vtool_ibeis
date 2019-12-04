#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import sys
import utool as ut


def run_tests():
    # Build module list and run tests
    import sys
    exclude_doctests_fnames = set([
    ])
    exclude_dirs = [
        '_broken',
        'old',
        'tests',
        'timeits',
        '_scripts',
        '_timeits',
        '_doc',
        'notebook',
    ]
    import vtool_ibeis as vt
    from os.path import dirname
    #dpath_list = ['vtool_ibeis']
    if ut.in_pyinstaller_package():
        # HACK, find_doctestable_modnames does not work in pyinstaller
        """
        import utool as ut
        import vtool_ibeis as vt
        dpath_list = [dirname(vt.__file__)]
        doctest_modname_list = ut.find_doctestable_modnames(
            dpath_list, exclude_doctests_fnames, exclude_dirs)
        print(ut.indent('doctest_modname_list = ' + ub.repr2(doctest_modname_list), ' ' * 8))

        """
        doctest_modname_list = [
            'vtool_ibeis.spatial_verification',
            'vtool_ibeis.constrained_matching',
            'vtool_ibeis.coverage_kpts',
            'vtool_ibeis.image',
            'vtool_ibeis.histogram',
            'vtool_ibeis.chip',
            'vtool_ibeis.distance',
            'vtool_ibeis.coverage_grid',
            'vtool_ibeis.linalg',
            'vtool_ibeis.geometry',
            'vtool_ibeis.other',
            'vtool_ibeis.util_math',
            'vtool_ibeis.score_normalization',
            'vtool_ibeis.test_constrained_matching',
            'vtool_ibeis.keypoint',
            'vtool_ibeis.sver_c_wrapper',
            'vtool_ibeis.quality_classifier',
            'vtool_ibeis.features',
            'vtool_ibeis.nearest_neighbors',
            'vtool_ibeis.segmentation',
            'vtool_ibeis.exif',
            'vtool_ibeis.patch',
            'vtool_ibeis.confusion',
            'vtool_ibeis.blend',
            'vtool_ibeis.clustering2',
            'vtool_ibeis.matching',
        ]
    else:
        dpath_list = [dirname(vt.__file__)]
        doctest_modname_list = ut.find_doctestable_modnames(
            dpath_list, exclude_doctests_fnames, exclude_dirs)

    coverage = ut.get_argflag(('--coverage', '--cov',))
    if coverage:
        import coverage
        cov = coverage.Coverage(source=doctest_modname_list)
        cov.start()
        print('Starting coverage')

        exclude_lines = [
            'pragma: no cover',
            'def __repr__',
            'if self.debug:',
            'if settings.DEBUG',
            'raise AssertionError',
            'raise NotImplementedError',
            'if 0:',
            'if ut.VERBOSE',
            'if _debug:',
            'if __name__ == .__main__.:',
            'print(.*)',
        ]
        for line in exclude_lines:
            cov.exclude(line)

    modname_list2 = []
    for modname in doctest_modname_list:
        try:
            exec('import ' + modname, globals(), locals())
        except ImportError as ex:
            ut.printex(ex)
            if not ut.in_pyinstaller_package():
                raise
        else:
            modname_list2.append(modname)

    if coverage:
        print('Stoping coverage')
        cov.stop()
        print('Saving coverage')
        cov.save()
        print('Generating coverage html report')
        cov.html_report()

    module_list = [sys.modules[name] for name in modname_list2]
    nPass, nTotal, failed_cmd_list = ut.doctest_module_list(module_list)
    if nPass != nTotal:
        return 1
    else:
        return 0

if __name__ == '__main__':
    import multiprocessing
    ut.change_term_title('RUN VTOOL TESTS')
    multiprocessing.freeze_support()
    retcode = run_tests()
    sys.exit(retcode)
