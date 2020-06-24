# -*- coding: utf-8 -*-
# def test_sver_wrapper2():
#     r"""
#     Example:
#         >>> # ENABLE_DOCTEST
#         >>> from vtool.sver_c_wrapper import *  # NOQA
#         >>> result = test_sver_wrapper2()
#         >>> print(result)
#     """
#     import vtool
#     import vtool.tests.testdata_nondeterm_sver
#     kpts1, kpts2, fm, xy_thresh, scale_thresh, ori_thresh, dlen_sqrd2, min_nInliers, match_weights, full_homog_checks = vtool.tests.testdata_nondeterm_sver.testdata_nondeterm_sver()
#     inliers_list = []
#     homog_inliers_list = []

#     for x in range(10):
#         sv_tup = vtool.spatially_verify_kpts(
#             kpts1, kpts2, fm, xy_thresh, scale_thresh, ori_thresh,
#             dlen_sqrd2, min_nInliers, match_weights=match_weights,
#             full_homog_checks=full_homog_checks, returnAff=True)
#         aff_inliers = sv_tup[3]
#         inliers_list.append(str(aff_inliers))
#         homog_inliers_list.append(str(sv_tup[0]))

#         #print(sv_tup[0])
#         #print(sv_tup[3])
#     print('unique cases affine inliers: ' + ub.repr2(list(set(inliers_list))))
#     print('unique cases homog inliers: ' + ub.repr2(list(set(homog_inliers_list))))


# def test_sver_wrapper():
#     """
#     Test to ensure cpp and python agree and that cpp is faster

#     Example:
#         >>> # ENABLE_DOCTEST
#         >>> from vtool.sver_c_wrapper import *  # NOQA
#         >>> test_sver_wrapper()

#     Ignore:
#         %timeit call_python_version(*args)
#         %timeit get_affine_inliers_cpp(*args)
#     """
#     import vtool.spatial_verification as sver
#     import vtool.demodata as demodata
#     xy_thresh_sqrd    = ktool.KPTS_DTYPE(.4)
#     scale_thresh_sqrd = ktool.KPTS_DTYPE(2.0)
#     ori_thresh        = ktool.KPTS_DTYPE(TAU / 4.0)
#     keys = 'xy_thresh_sqrd, scale_thresh_sqrd, ori_thresh'.split(', ')
#     print(ub.repr2(ut.dict_subset(locals(), keys)))

#     def report_errors():
#         pass

#     if ut.get_argflag('--demodata'):
#         testtup = demodata.testdata_dummy_matches()
#         (kpts1, kpts2, fm_input, fs_input, rchip1, rchip2) = testtup
#         fm_input = fm_input.astype(fm_dtype)
#         #fm_input = fm_input[0:10].astype(fm_dtype)
#         #fs_input = fs_input[0:10].astype(np.float32)
#     else:
#         fname1 = ut.get_argval('--fname1', type_=str, default='easy1.png')
#         fname2 = ut.get_argval('--fname2', type_=str, default='easy2.png')
#         testtup = demodata.testdata_ratio_matches(fname1, fname2)
#         (kpts1, kpts2, fm_input, fs_input, rchip1, rchip2) = testtup

#     # pack up call to aff hypothesis
#     import vtool as vt
#     import scipy.stats.mstats
#     scales1 = vt.get_scales(kpts1.take(fm_input.T[0], axis=0))
#     scales2 = vt.get_scales(kpts2.take(fm_input.T[1], axis=0))
#     #fs_input = 1 / scipy.stats.mstats.gmean(np.vstack((scales1, scales2)))
#     fs_input = scipy.stats.mstats.gmean(np.vstack((scales1, scales2)))
#     print('fs_input = ' + ub.repr2(fs_input))
#     #fs_input[0:-9] = 0
#     #fs_input = np.ones(len(fm_input), dtype=fs_dtype)
#     #ut.embed()
#     #fs_input = scales1 * scales2
#     args = (kpts1, kpts2, fm_input, fs_input, xy_thresh_sqrd, scale_thresh_sqrd, ori_thresh)

#     ex_list = []

#     try:
#         with ut.Indenter('[TEST1] '):
#             inlier_tup = vt.compare_implementations(
#                 sver.get_affine_inliers,
#                 get_affine_inliers_cpp,
#                 args, lbl1='py', lbl2='c',
#                 output_lbl=('aff_inliers_list', 'aff_errors_list', 'Aff_mats')
#             )
#             out_inliers, out_errors, out_mats = inlier_tup
#     except AssertionError as ex:
#         ex_list.append(ex)
#         raise

#     try:
#         import functools
#         with ut.Indenter('[TEST2] '):
#             bestinlier_tup = vt.compare_implementations(
#                 functools.partial(sver.get_best_affine_inliers, forcepy=True),
#                 get_best_affine_inliers_cpp,
#                 args, show_output=True, lbl1='py', lbl2='c',
#                 output_lbl=('bestinliers', 'besterror', 'bestmat')
#             )
#             bestinliers, besterror, bestmat = bestinlier_tup
#     except AssertionError as ex:
#         ex_list.append(ex)
#         raise

#     if len(ex_list) > 0:
#         raise AssertionError('some tests failed. see previous stdout')

#     #num_inliers_list = np.array(map(len, out_inliers_c))
#     #best_argx = num_inliers_list.argmax()
#     ##best_inliers_py = out_inliers_py[best_argx]
#     #best_inliers_c = out_inliers_c[best_argx]
#     if ut.show_was_requested():
#         import wbia.plottool as pt
#         fm_output = fm_input.take(bestinliers, axis=0)
#         fnum = pt.next_fnum()
#         pt.figure(fnum=fnum, doclf=True, docla=True)
#         pt.show_chipmatch2(rchip1, rchip2, kpts1, kpts2, fm_input, ell_linewidth=5, fnum=fnum, pnum=(2, 1, 1))
#         pt.show_chipmatch2(rchip1, rchip2, kpts1, kpts2, fm_output, ell_linewidth=5, fnum=fnum, pnum=(2, 1, 2))
#         pt.show_if_requested()


# def call_hello():
#     lib = C.cdll['./sver.so']
#     hello = lib['hello_world']
#     hello()
