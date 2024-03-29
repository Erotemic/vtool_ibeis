#!/usr/bin/env python
from __future__ import absolute_import, division, print_function
import utool as ut
import vtool_ibeis.spatial_verification as sver
import numpy as np
import vtool_ibeis.demodata as demodata
import vtool_ibeis.keypoint as ktool  # NOQA
import vtool_ibeis.linalg as ltool  # NOQA


xy_thresh = ktool.KPTS_DTYPE(.009)
scale_thresh_sqrd = ktool.KPTS_DTYPE(2)
TAU = np.pi * 2.0  # References: tauday.com
ori_thresh = ktool.KPTS_DTYPE(TAU / 4.0)


# def test_sver():
#     nShow = ut.get_argval('--nShow', int, 1)
#     chip1, chip2, kpts1, kpts2, fm = get_dummy_test_vars()
#     demo_sver(chip1, chip2, kpts1, kpts2, fm, nShow)


def demo_sver(chip1, chip2, kpts1, kpts2, fm, nShow=6):
    r"""
    Args:
        chip1 (ndarray[uint8_t, ndim=2]):  annotation image data
        chip2 (ndarray[uint8_t, ndim=2]):  annotation image data
        kpts1 (ndarray[float32_t, ndim=2]):  keypoints
        kpts2 (ndarray[float32_t, ndim=2]):  keypoints
        fm (list):  list of feature matches as tuples (qfx, dfx)
        nShow (int):

    Example0:
        >>> # DISABLE_DOCTEST
        >>> # xdoctest: +REQUIRES(module:plottool)
        >>> import plottool_ibeis as pt
        >>> # build test data
        >>> nShow = ut.get_argval('--nShow', int, 1)
        >>> chip1, chip2, kpts1, kpts2, fm = get_dummy_test_vars()
        >>> # execute function
        >>> result = demo_sver(chip1, chip2, kpts1, kpts2, fm, nShow)
        >>> # verify results
        >>> print(result)
        >>> pt.show_if_requested()

    Example1:
        >>> # DISABLE_DOCTEST
        >>> # xdoctest: +REQUIRES(module:plottool)
        >>> import plottool_ibeis as pt
        >>> # build test data
        >>> nShow = ut.get_argval('--nShow', int, 1)
        >>> chip1, chip2, kpts1, kpts2, fm = get_dummy_test_vars1()
        >>> # execute function
        >>> result = demo_sver(chip1, chip2, kpts1, kpts2, fm, nShow)
        >>> # verify results
        >>> print(result)
        >>> pt.show_if_requested()
    """

    xy_thresh_sqrd = ktool.get_diag_extent_sqrd(kpts2) * xy_thresh

    def pack_errors(xy_err, scale_err, ori_err):
        """ makes human readable errors """
        def _pack(bits, errs, thresh):
            return ut.indentjoin(['%5s %f < %f' % (bit, err, thresh) for
                                  (bit, err) in zip(bits, errs)])
        xy_flag = xy_err < xy_thresh_sqrd
        scale_flag = scale_err < scale_thresh_sqrd
        ori_flag = ori_err < ori_thresh
        errors_dict = {
            'xy_err':     _pack(xy_flag, np.sqrt(xy_err), np.sqrt(xy_thresh_sqrd)),
            'scale_err':  _pack(scale_flag, np.sqrt(scale_err), np.sqrt(scale_thresh_sqrd)),
            'ori_err':    _pack(ori_flag, ori_err, ori_thresh),
        }
        return errors_dict

    # Test each affine hypothesis
    #assert kpts1.dtype == ktool.KPTS_DTYPE, 'bad cast somewhere kpts1.dtype=%r' % (kpts1.dtype)
    #assert kpts2.dtype == ktool.KPTS_DTYPE, 'bad cast somewhere kpts2.dtype=%r' % (kpts2.dtype)
    #assert xy_thresh_sqrd.dtype == ktool.KPTS_DTYPE, 'bad cast somewhere
    #xy_thresh_sqrd.dtype=%r' % (xy_thresh_sqrd.dtype)
    aff_hypo_tups = sver.get_affine_inliers(kpts1, kpts2, fm, xy_thresh_sqrd,
                                            scale_thresh_sqrd, ori_thresh)
    inliers_list, errors_list, Aff_mats = aff_hypo_tups

    # Determine best hypothesis
    nInliers_list = np.array(list(map(len, inliers_list)))
    best_mxs = nInliers_list.argsort()[::-1]

    for fnum, mx in enumerate(best_mxs[0:min(len(best_mxs), nShow)]):
        Aff = Aff_mats[mx]
        aff_inliers = inliers_list[mx]
        if ut.get_argflag('--print-error'):
            errors = pack_errors(*errors_list[mx])  # NOQA
            print(ut.repr2(errors, strvals=True))

        homog_inliers, homog_errors, H = sver.get_homography_inliers(kpts1,
                                                                     kpts2, fm,
                                                                     aff_inliers,
                                                                     xy_thresh_sqrd)

        kpts1_At = ktool.transform_kpts(kpts1, Aff)
        kpts1_Ht = ktool.transform_kpts(kpts1, H)
        kpts = kpts1
        M = H

        homog_tup = (homog_inliers, H)
        aff_tup = (aff_inliers, Aff)

        _args = (chip1, chip2, kpts1, kpts2, fm)
        _kw = dict(show_assign=True, show_kpts=True, mx=mx, fnum=fnum * 3)
        from plottool_ibeis import draw_func2 as df2
        from plottool_ibeis import draw_sv
        draw_sv.show_sv(*_args, aff_tup=aff_tup, homog_tup=homog_tup, **_kw)
        #draw_sv.show_sv(*_args, aff_tup=aff_tup, mx=mx, fnum=fnum * 3)
        #draw_sv.show_sv(*_args, homog_tup=homog_tup, mx=mx, fnum=3)

        df2.set_figtitle('# %r inliers (in rects, hypo in bold)' % (nInliers_list[mx],))
    return locals()


def get_dummy_test_vars():
    kpts1 = demodata.perterbed_grid_kpts(seed=12, damping=1.2, dtype=np.float64)
    kpts2 = demodata.perterbed_grid_kpts(seed=24, damping=1.6, dtype=np.float64)
    assert kpts1.dtype == np.float64
    assert kpts2.dtype == np.float64
    chip1 = demodata.get_kpts_dummy_img(kpts1)
    chip2 = demodata.get_kpts_dummy_img(kpts2)
    #kpts2 = ktool.get_grid_kpts()
    fm = demodata.make_dummy_fm(len(kpts1))
    return chip1, chip2, kpts1, kpts2, fm


def get_dummy_test_vars1(fname1='easy1.png', fname2='easy2.png'):
    import utool as ut
    from vtool_ibeis import image as gtool
    from vtool_ibeis import features as feattool
    fpath1 = ut.grab_test_imgpath(fname1)
    fpath2 = ut.grab_test_imgpath(fname2)
    kpts1, vecs1 = feattool.extract_features(fpath1)
    kpts2, vecs2 = feattool.extract_features(fpath2)
    chip1 = gtool.imread(fpath1)
    chip2 = gtool.imread(fpath2)
    #chip1_shape = vt.gtool.open_image_size(fpath1)
    #chip2_shape = gtool.open_image_size(fpath2)
    #dlen_sqrd2 = chip2_shape[0] ** 2 + chip2_shape[1]
    #testtup = (rchip1, rchip2, kpts1, vecs1, kpts2, vecs2, dlen_sqrd2)
    import vtool_ibeis as vt
    checks = 800
    flann_params = {
        'algorithm': 'kdtree',
        'trees': 8
    }
    #pseudo_max_dist_sqrd = (np.sqrt(2) * 512) ** 2
    pseudo_max_dist_sqrd = 2 * (512 ** 2)
    flann = vt.flann_cache(vecs1, flann_params=flann_params)
    try:
        from vtool_ibeis._pyflann_backend import pyflann
    except Exception:
        import pytest
        pytest.skip()
    try:
        fx2_to_fx1, _fx2_to_dist = flann.nn_index(vecs2, num_neighbors=2, checks=checks)
    except pyflann.FLANNException:
        print('vecs1.shape = %r' % (vecs1.shape,))
        print('vecs2.shape = %r' % (vecs2.shape,))
        print('vecs1.dtype = %r' % (vecs1.dtype,))
        print('vecs2.dtype = %r' % (vecs2.dtype,))
        raise
    fx2_to_dist = np.divide(_fx2_to_dist, pseudo_max_dist_sqrd)
    fx2_to_ratio = np.divide(fx2_to_dist.T[0], fx2_to_dist.T[1])
    ratio_thresh = .625
    fx2_to_isvalid = fx2_to_ratio < ratio_thresh
    fx2_m = np.where(fx2_to_isvalid)[0]
    fx1_m = fx2_to_fx1.T[0].take(fx2_m)
    #fs_RAT = np.subtract(1.0, fx2_to_ratio.take(fx2_m))
    fm_RAT = np.vstack((fx1_m, fx2_m)).T
    fm = fm_RAT
    return chip1, chip2, kpts1, kpts2, fm


def get_stashed_test_vars():
    import utool as ut
    chip1, chip2, kpts1, kpts2, fm, homog_tup, aff_tup = ut.load_testdata(
        'chip1', 'chip2', 'kpts1', 'kpts2', 'fm', 'homog_tup', 'aff_tup')
    return chip1, chip2, kpts1, kpts2, fm


if __name__ == '__main__':
    """
    CommandLine:
        xdoctest -m tests.test_spatial_verification
    """
    import xdoctest
    xdoctest.doctest_module(__file__)
