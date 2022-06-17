#!/usr/bin/env python
"""
wraps c implementations slower parts of spatial verification

CommandLine:
    python -m vtool_ibeis.sver_c_wrapper --rebuild-sver
    python -m vtool_ibeis.sver_c_wrapper --rebuild-sver --allexamples
    python -m vtool_ibeis.sver_c_wrapper --allexamples

    python -m vtool_ibeis.sver_c_wrapper --test-test_sver_wrapper --rebuild-sver

Example:
    >>> # xdoctest: +REQUIRES(module:vtool_ibeis_ext)
    >>> import numpy as np
    >>> kpts1 = np.array([[ 3.2e+01,  2.7e+01,  1.7e+01,  5.0e+00,  2.1e+01,  6.2e+00],
    >>>                   [ 1.3e+02,  2.3e+01,  2.0e+01,  2.7e+00,  2.1e+01,  6.3e+00],
    >>>                   [ 2.3e+02,  2.4e+01,  1.7e+01, -9.2e+00,  1.6e+01,  4.7e-01],
    >>>                   [ 3.0e+01,  1.3e+02,  1.6e+01, -9.2e+00,  1.8e+01,  5.6e+00],
    >>>                   [ 1.3e+02,  1.4e+02,  1.9e+01, -1.6e-01,  2.1e+01,  1.1e-01],
    >>>                   [ 2.3e+02,  1.3e+02,  1.9e+01, -1.1e+00,  2.0e+01,  4.8e-02],
    >>>                   [ 3.5e+01,  2.2e+02,  1.8e+01, -3.0e+00,  2.0e+01,  1.8e-01],
    >>>                   [ 1.4e+02,  2.3e+02,  1.8e+01, -2.4e+00,  2.0e+01,  6.0e+00],
    >>>                   [ 2.3e+02,  2.3e+02,  2.3e+01,  1.3e+00,  1.9e+01,  4.4e-01]], dtype=np.float64)
    >>> kpts2 = np.array([[3.4e+01, 2.8e+01, 2.0e+01, 1.6e+00, 1.7e+01, 1.8e-02],
    >>>                   [1.3e+02, 2.7e+01, 2.1e+01, 4.4e+00, 2.0e+01, 6.3e+00],
    >>>                   [2.3e+02, 2.6e+01, 2.0e+01, 3.8e+00, 2.0e+01, 7.3e-03],
    >>>                   [3.2e+01, 1.3e+02, 2.3e+01, 1.1e+00, 2.2e+01, 6.0e+00],
    >>>                   [1.2e+02, 1.3e+02, 1.9e+01, 1.6e+00, 2.3e+01, 6.2e+00],
    >>>                   [2.3e+02, 1.4e+02, 1.8e+01, 4.5e+00, 1.6e+01, 2.7e-01],
    >>>                   [3.3e+01, 2.3e+02, 2.0e+01, 2.0e+00, 1.9e+01, 1.7e-01],
    >>>                   [1.3e+02, 2.3e+02, 2.1e+01, 4.0e+00, 2.1e+01, 1.1e-01],
    >>>                   [2.3e+02, 2.3e+02, 1.6e+01, 2.5e+00, 2.2e+01, 6.2e+00]], dtype=np.float64)
    >>> fm = np.array([[0, 0],[1, 1],[2, 2],[3, 3],[4, 4],[5, 5],[6, 6],[7, 7],[8, 8]], dtype=np.int64)
    >>> fs = np.array([1., 1., 1., 1., 1., 1., 1., 1., 1.], dtype=np.float64)
    >>> xy_thresh_sqrd = 100
    >>> scale_thresh_sqrd = 100
    >>> ori_thresh = 100
    >>> from vtool_ibeis.sver_c_wrapper import get_affine_inliers_cpp
    >>> from vtool_ibeis.sver_c_wrapper import get_best_affine_inliers_cpp
    >>> out_inliers, out_errors, out_mats = get_affine_inliers_cpp(kpts1, kpts2, fm, fs, xy_thresh_sqrd, scale_thresh_sqrd, ori_thresh)
    >>> out_inliers, out_errors, out_mats = get_best_affine_inliers_cpp(kpts1, kpts2, fm, fs, xy_thresh_sqrd, scale_thresh_sqrd, ori_thresh)
"""
from __future__ import absolute_import, division, print_function


def get_affine_inliers_cpp(kpts1, kpts2, fm, fs, xy_thresh_sqrd, scale_thresh_sqrd, ori_thresh):
    """
    Example:
        kpts1 =
    """
    from vtool_ibeis_ext import sver_c_wrapper
    out_inliers, out_errors, out_mats = sver_c_wrapper.get_affine_inliers_cpp(
        kpts2, kpts2, fm, fs, xy_thresh_sqrd, scale_thresh_sqrd, ori_thresh)
    return out_inliers, out_errors, out_mats


def get_best_affine_inliers_cpp(kpts1, kpts2, fm, fs, xy_thresh_sqrd,
                                scale_thresh_sqrd, ori_thresh):
    from vtool_ibeis_ext import sver_c_wrapper
    out_inliers, out_errors, out_mat = sver_c_wrapper.get_best_affine_inliers_cpp(
        kpts1, kpts2, fm, fs, xy_thresh_sqrd, scale_thresh_sqrd, ori_thresh)
    return out_inliers, out_errors, out_mat


if __name__ == '__main__':
    """
    CommandLine:
        xdoctest -m vtool_ibeis.sver_c_wrapper
    """
    import xdoctest
    xdoctest.doctest_module(__file__)
