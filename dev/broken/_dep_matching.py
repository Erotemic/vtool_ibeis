def marge_matches(fm_A, fm_B, fsv_A, fsv_B):
    """ combines feature matches from two matching algorithms

    Args:
        fm_A (ndarray[ndims=2]): type A feature matches
        fm_B (ndarray[ndims=2]): type B feature matches
        fsv_A (ndarray[ndims=2]): type A feature scores
        fsv_B (ndarray[ndims=2]): type B feature scores

    Returns:
        tuple: (fm_both, fs_both)

    CommandLine:
        python -m vtool.matching --test-marge_matches

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool.matching import *  # NOQA
        >>> fm_A  = np.array([[ 15, 17], [ 54, 29], [ 95, 111], [ 25, 125], [ 97, 125]], dtype=np.int32)
        >>> fm_B  = np.array([[ 11, 21], [ 15, 17], [ 25, 125], [ 30,  32]], dtype=np.int32)
        >>> fsv_A = np.array([[ .1, .2], [1.0, .9], [.8,  .2],  [.1, .1], [1.0, .9]], dtype=np.float32)
        >>> fsv_B = np.array([[.12], [.3], [.5], [.7]], dtype=np.float32)
        >>> # execute function
        >>> (fm_both, fs_both) = marge_matches(fm_A, fm_B, fsv_A, fsv_B)
        >>> # verify results
        >>> result = ub.repr2((fm_both, fs_both), precision=3)
        >>> print(result)
        (
            np.array([[ 15,  17],
                      [ 25, 125],
                      [ 54,  29],
                      [ 95, 111],
                      [ 97, 125],
                      [ 11,  21],
                      [ 30,  32]], dtype=np.int32),
            np.array([[ 0.1 ,  0.2 ,  0.3 ],
                      [ 0.1 ,  0.1 ,  0.5 ],
                      [ 1.  ,  0.9 ,   nan],
                      [ 0.8 ,  0.2 ,   nan],
                      [ 1.  ,  0.9 ,   nan],
                      [  nan,   nan,  0.12],
                      [  nan,   nan,  0.7 ]], dtype=np.float64),
        )
    """
    # Flag rows found in both fmA and fmB
    # that are intersecting (both) or unique (only)
    import vtool as vt

    flags_both_A, flags_both_B = vt.intersect2d_flags(fm_A, fm_B)
    flags_only_A = np.logical_not(flags_both_A)
    flags_only_B = np.logical_not(flags_both_B)
    # independent matches
    fm_both_AB = fm_A.compress(flags_both_A, axis=0)
    fm_only_A = fm_A.compress(flags_only_A, axis=0)
    fm_only_B = fm_B.compress(flags_only_B, axis=0)
    # independent scores
    fsv_both_A = fsv_A.compress(flags_both_A, axis=0)
    fsv_both_B = fsv_B.compress(flags_both_B, axis=0)
    fsv_only_A = fsv_A.compress(flags_only_A, axis=0)
    fsv_only_B = fsv_B.compress(flags_only_B, axis=0)
    # build merge offsets
    offset1 = len(fm_both_AB)
    offset2 = offset1 + len(fm_only_A)
    offset3 = offset2 + len(fm_only_B)
    # Merge feature matches
    fm_merged = np.vstack([fm_both_AB, fm_only_A, fm_only_B])
    # Merge feature scores
    num_rows = fm_merged.shape[0]
    num_cols_A = fsv_A.shape[1]
    num_cols_B = fsv_B.shape[1]
    num_cols = num_cols_A + num_cols_B
    fsv_merged = np.full((num_rows, num_cols), np.nan)
    fsv_merged[0:offset1, 0:num_cols_A] = fsv_both_A
    fsv_merged[0:offset1, num_cols_A:] = fsv_both_B
    fsv_merged[offset1:offset2, 0:num_cols_A] = fsv_only_A
    fsv_merged[offset2:offset3, num_cols_A:] = fsv_only_B
    return fm_merged, fsv_merged


def ensure_fsv_list(fsv_list):
    """ ensure fs is at least Nx1 """
    return [fsv[:, None] if len(fsv.shape) == 1 else fsv for fsv in fsv_list]


from __future__ import absolute_import, division, print_function

# from six.moves import range
import utool as ut
import six  # NOQA
import numpy as np

# from vtool import keypoint as ktool
from vtool import coverage_kpts
from vtool import spatial_verification as sver
from vtool import matching

# import numpy.linalg as npl
# import scipy.sparse as sps
# import scipy.sparse.linalg as spsl
# from numpy.core.umath_tests import matrix_multiply
# import vtool.keypoint as ktool
# import vtool.linalg as ltool
# profile = ut.profile


def assign_nearest_neighbors(vecs1, vecs2, K=2):
    import vtool as vt
    from vtool._pyflann_backend import pyflann

    checks = 800
    flann_params = {'algorithm': 'kdtree', 'trees': 8}
    # pseudo_max_dist_sqrd = (np.sqrt(2) * 512) ** 2
    # pseudo_max_dist_sqrd = 2 * (512 ** 2)
    flann = vt.flann_cache(vecs1, flann_params=flann_params)
    try:
        fx2_to_fx1, fx2_to_dist = matching.normalized_nearest_neighbors(
            flann, vecs2, K, checks
        )
        # fx2_to_fx1, _fx2_to_dist = flann.nn_index(vecs2, num_neighbors=K, checks=checks)
    except pyflann.FLANNException:
        print('vecs1.shape = %r' % (vecs1.shape,))
        print('vecs2.shape = %r' % (vecs2.shape,))
        print('vecs1.dtype = %r' % (vecs1.dtype,))
        print('vecs2.dtype = %r' % (vecs2.dtype,))
        raise
    # fx2_to_dist = np.divide(_fx2_to_dist, pseudo_max_dist_sqrd)
    return fx2_to_fx1, fx2_to_dist


def baseline_vsone_ratio_matcher(testtup, cfgdict={}):
    r"""
    spatially constrained ratio matching

    CommandLine:
        python -m vtool.constrained_matching --test-spatially_constrianed_matcher

    Example:
        >>> # DISABLE_DOCTEST
        >>> import wbia.plottool as pt
        >>> from vtool.constrained_matching import *  # NOQA
        >>> import vtool as vt
        >>> testtup = testdata_matcher()
        >>> # execute function
        >>> basetup, base_meta = baseline_vsone_ratio_matcher(testtup)
        >>> # verify results
        >>> print(basetup)
    """
    rchip1, rchip2, kpts1, vecs1, kpts2, vecs2, dlen_sqrd2 = testtup
    return baseline_vsone_ratio_matcher_(
        kpts1, vecs1, kpts2, vecs2, dlen_sqrd2, cfgdict={}
    )


def spatially_constrianed_matcher(testtup, basetup, cfgdict={}):
    r"""
    spatially constrained ratio matching

    CommandLine:
        python -m vtool.constrained_matching --test-spatially_constrianed_matcher

    Example:
        >>> # DISABLE_DOCTEST
        >>> import wbia.plottool as pt
        >>> from vtool.constrained_matching import *  # NOQA
        >>> import vtool as vt
        >>> testtup = testdata_matcher()
        >>> basetup, base_meta = baseline_vsone_ratio_matcher(testtup)
        >>> # execute function
        >>> nexttup, next_meta = spatially_constrianed_matcher(testtup, basetup)
        >>> # verify results
        >>> print(nexttup)
    """
    (rchip1, rchip2, kpts1, vecs1, kpts2, vecs2, dlen_sqrd2) = testtup
    (fm_ORIG, fs_ORIG, fm_RAT, fs_RAT, fm_SV, fs_SV, H_RAT) = basetup
    return spatially_constrianed_matcher_(
        kpts1, vecs1, kpts2, vecs2, dlen_sqrd2, H_RAT, cfgdict={}
    )


def baseline_vsone_ratio_matcher_(kpts1, vecs1, kpts2, vecs2, dlen_sqrd2, cfgdict={}):
    r"""
    Args:
        vecs1 (ndarray[uint8_t, ndim=2]): SIFT descriptors
        vecs2 (ndarray[uint8_t, ndim=2]): SIFT descriptors
        kpts1 (ndarray[float32_t, ndim=2]):  keypoints
        kpts2 (ndarray[float32_t, ndim=2]):  keypoints

    Ignore:
        %pylab qt4
        import wbia.plottool as pt
        pt.imshow(rchip1)
        pt.draw_kpts2(kpts1)

        pt.show_chipmatch2(rchip1, rchip2, kpts1, kpts2, fm=fm, fs=fs)
        pt.show_chipmatch2(rchip1, rchip2, kpts1, kpts2, fm=fm, fs=fs)
    """
    # import vtool as vt
    sver_xy_thresh = cfgdict.get('sver_xy_thresh', 0.01)
    ratio_thresh = cfgdict.get('ratio_thresh', 0.625)
    # ratio_thresh =  .99
    # GET NEAREST NEIGHBORS
    fx2_to_fx1, fx2_to_dist = assign_nearest_neighbors(vecs1, vecs2, K=2)
    assigntup = matching.assign_unconstrained_matches(fx2_to_fx1, fx2_to_dist)
    fx2_match, fx1_match, fx1_norm, match_dist, norm_dist = assigntup
    fm_ORIG = np.vstack((fx1_match, fx2_match)).T
    fs_ORIG = 1 - np.divide(match_dist, norm_dist)
    # APPLY RATIO TEST
    fm_RAT, fs_RAT, fm_norm_RAT = matching.ratio_test(
        fx2_match, fx1_match, fx1_norm, match_dist, norm_dist, ratio_thresh
    )
    # SPATIAL VERIFICATION FILTER
    # with ut.EmbedOnException():
    match_weights = np.ones(len(fm_RAT))
    svtup = sver.spatially_verify_kpts(
        kpts1, kpts2, fm_RAT, sver_xy_thresh, dlen_sqrd2, match_weights=match_weights
    )
    if svtup is not None:
        (homog_inliers, homog_errors, H_RAT) = svtup[0:3]
    else:
        H_RAT = np.eye(3)
        homog_inliers = []
    fm_SV = fm_RAT[homog_inliers]
    fs_SV = fs_RAT[homog_inliers]
    fm_norm_SV = fm_norm_RAT[homog_inliers]

    base_tup = (fm_ORIG, fs_ORIG, fm_RAT, fs_RAT, fm_SV, fs_SV, H_RAT)
    base_meta = (fm_norm_RAT, fm_norm_SV)
    return base_tup, base_meta


def spatially_constrianed_matcher_(
    kpts1, vecs1, kpts2, vecs2, dlen_sqrd2, H_RAT, cfgdict={}
):
    # import vtool as vt

    # match_xy_thresh = .1
    # sver_xy_thresh = .01
    # ratio_thresh2 = .8
    # Observation, scores don't change above K=7
    # on easy test case
    # search_K = 7  # 3
    search_K = cfgdict.get('search_K', 7)
    ratio_thresh2 = cfgdict.get('ratio_thresh2', 0.8)
    sver_xy_thresh2 = cfgdict.get('sver_xy_thresh2', 0.01)
    normalizer_mode = cfgdict.get('normalizer_mode', 'far')
    match_xy_thresh = cfgdict.get('match_xy_thresh', 0.1)

    # ASSIGN CANDIDATES
    # Get candidate nearest neighbors
    fx2_to_fx1, fx2_to_dist = assign_nearest_neighbors(vecs1, vecs2, K=search_K)

    # COMPUTE CONSTRAINTS
    # normalizer_mode = 'far'
    constrain_tup = spatially_constrain_matches(
        dlen_sqrd2,
        kpts1,
        kpts2,
        H_RAT,
        fx2_to_fx1,
        fx2_to_dist,
        match_xy_thresh,
        normalizer_mode=normalizer_mode,
    )
    (fm_SC, fm_norm_SC, match_dist, norm_dist) = constrain_tup
    fx2_match = fm_SC.T[1]
    fx1_match = fm_SC.T[1]
    fx1_norm = fm_norm_SC.T[1]

    fm_SCR, fs_SCR, fm_norm_SCR = matching.ratio_test(
        fx2_match, fx1_match, fx1_norm, match_dist, norm_dist, ratio_thresh2
    )
    fs_SC = 1 - np.divide(match_dist, norm_dist)  # NOQA
    # fm_SCR, fs_SCR, fm_norm_SCR = ratio_test2(match_dist, norm_dist, fm_SC,
    #                                                fm_norm_SC, ratio_thresh2)

    # Another round of verification
    match_weights = np.ones(len(fm_SCR))
    svtup = sver.spatially_verify_kpts(
        kpts1, kpts2, fm_SCR, sver_xy_thresh2, dlen_sqrd2, match_weights=match_weights
    )
    if svtup is not None:
        (homog_inliers, homog_errors, H_SCR) = svtup[0:3]
    else:
        H_SCR = np.eye(3)
        homog_inliers = []
    fm_SCRSV = fm_SCR[homog_inliers]
    fs_SCRSV = fs_SCR[homog_inliers]

    fm_norm_SVSCR = fm_norm_SCR[homog_inliers]

    nexttup = (fm_SC, fs_SC, fm_SCR, fs_SCR, fm_SCRSV, fs_SCRSV, H_SCR)
    next_meta = (fm_norm_SC, fm_norm_SCR, fm_norm_SVSCR)
    return nexttup, next_meta


# def ratio_test(fx2_to_fx1, fx2_to_dist, ratio_thresh):
#    fx2_to_ratio = np.divide(fx2_to_dist.T[0], fx2_to_dist.T[1])
#    fx2_to_isvalid = fx2_to_ratio < ratio_thresh
#    fx2_m = np.where(fx2_to_isvalid)[0]
#    fx1_m = fx2_to_fx1.T[0].take(fx2_m)
#    fs_RAT = np.subtract(1.0, fx2_to_ratio.take(fx2_m))
#    fm_RAT = np.vstack((fx1_m, fx2_m)).T
#    # return normalizer info as well
#    fx1_m_normalizer = fx2_to_fx1.T[1].take(fx2_m)
#    fm_norm_RAT = np.vstack((fx1_m_normalizer, fx2_m)).T
#    return fm_RAT, fs_RAT, fm_norm_RAT


# def ratio_test2(match_dist_list, norm_dist_list, fm_SC, fm_norm_SC, ratio_thresh2=.8):
#    ratio_list = np.divide(match_dist_list, norm_dist_list)
#    #ratio_thresh = .625
#    #ratio_thresh = .725
#    isvalid_list = np.less(ratio_list, ratio_thresh2)
#    valid_ratios = ratio_list[isvalid_list]
#    fm_SCR = fm_SC[isvalid_list]
#    fs_SCR = np.subtract(1.0, valid_ratios)  # NOQA
#    fm_norm_SCR = fm_norm_SC[isvalid_list]
#    #fm_SCR = np.vstack((fx1_m, fx2_m)).T  # NOQA
#    return fm_SCR, fs_SCR, fm_norm_SCR


def spatially_constrain_matches(
    dlen_sqrd2,
    kpts1,
    kpts2,
    H_RAT,
    fx2_to_fx1,
    fx2_to_dist,
    match_xy_thresh,
    normalizer_mode='far',
):
    r"""
    helper for spatially_constrianed_matcher
    OLD FUNCTION

    Args:
        dlen_sqrd2 (?):
        kpts1 (ndarray[float32_t, ndim=2]):  keypoints
        kpts2 (ndarray[float32_t, ndim=2]):  keypoints
        H_RAT (ndarray[float64_t, ndim=2]):  homography/perspective matrix
        fx2_to_fx1 (ndarray):
        fx2_to_dist (ndarray):
        match_xy_thresh (?): threshold is specified as a fraction of the diagonal chip length
        normalizer_mode (str):
    """
    # Find the normalized spatial error of all candidate matches
    #####

    # Filter out matches that could not be constrained

    if normalizer_mode == 'plus':
        norm_xy_bounds = (0, np.inf)
    elif normalizer_mode == 'far':
        norm_xy_bounds = (match_xy_thresh, np.inf)
    elif normalizer_mode == 'nearby':
        norm_xy_bounds = (0, match_xy_thresh)
    else:
        raise AssertionError('normalizer_mode=%r' % (normalizer_mode,))

    assigntup = matching.assign_spatially_constrained_matches(
        dlen_sqrd2,
        kpts1,
        kpts2,
        H_RAT,
        fx2_to_fx1,
        fx2_to_dist,
        match_xy_thresh,
        norm_xy_bounds=norm_xy_bounds,
    )

    fx2_match, fx1_match, fx1_norm, match_dist, norm_dist = assigntup

    fm_constrained = np.vstack((fx1_match, fx2_match)).T
    # return noramlizers as well
    fm_norm_constrained = np.vstack((fx1_norm, fx2_match)).T

    constraintup = (fm_constrained, fm_norm_constrained, match_dist, norm_dist)
    return constraintup


def compute_forgroundness(fpath1, kpts1, species='zebra_plains'):
    """
    hack in foregroundness
    """
    import pyrf
    import vtool as vt
    from os.path import exists

    # hack for getting a model (not entirely ibeis independent)
    trees_path = ut.get_app_resource_dir('ibeis', 'detectmodels', 'rf', species)
    tree_fpath_list = ut.glob(trees_path, '*.txt')
    detector = pyrf.Random_Forest_Detector()
    # TODO; might need to downsample
    forest = detector.forest(tree_fpath_list, verbose=False)
    gpath_list = [fpath1]
    output_gpath_list = [gpath + '.' + species + '.probchip.png' for gpath in gpath_list]
    detectkw = {
        'scale_list': [1.15, 1.0, 0.85, 0.7, 0.55, 0.4, 0.25, 0.1],
        'output_gpath_list': output_gpath_list,
        'mode': 1,  # mode one outputs probimage
    }
    results_iter = detector.detect(forest, gpath_list, **detectkw)
    results_list = list(results_iter)  # NOQA
    probchip_list = [
        vt.imread(gpath, grayscale=True) if exists(gpath) else None
        for gpath in output_gpath_list
    ]
    # vtpatch.get_warped_patches()
    fgweights_list = []
    kpts_list = [kpts1]
    for probchip, kpts in zip(probchip_list, kpts_list):
        patch_list = [
            vt.get_warped_patch(probchip, kp)[0].astype(np.float32) / 255.0 for kp in kpts
        ]
        weight_list = [vt.gaussian_average_patch(patch) for patch in patch_list]
        # weight_list = [patch.sum() / (patch.size) for patch in patch_list]
        weights = np.array(weight_list, dtype=np.float32)
        fgweights_list.append(weights)
    fgweights = fgweights_list[0]
    detector.free_forest(forest)
    return fgweights


def compute_distinctivness(vecs_list, species='zebra_plains'):
    """
    hack in distinctivness
    """
    from wbia.algo.hots import distinctiveness_normalizer

    cachedir = ut.get_app_resource_dir('ibeis', 'distinctiveness_model')
    dstcnvs_normer = distinctiveness_normalizer.DistinctivnessNormalizer(
        species, cachedir=cachedir
    )
    dstcnvs_normer.load(cachedir)
    dstncvs_list = [dstcnvs_normer.get_distinctiveness(vecs) for vecs in vecs_list]
    return dstncvs_list


@six.add_metaclass(ut.ReloadingMetaclass)
class Annot(object):
    """
    fpath1 = ut.grab_test_imgpath(fname1)
    fpath2 = ut.grab_test_imgpath(fname2)
    annot1 = Annot(fpath1)
    annot2 = Annot(fpath2)
    annot = annot1

    """

    def __init__(annot, fpath, species='zebra_plains'):
        annot.fpath = fpath
        annot.species = species
        annot.kpts = None
        annot.vecs = None
        annot.rchip = None
        annot.dstncvs = None
        annot.fgweights = None
        annot.dstncvs_mask = None
        annot.fgweight_mask = None
        annot.load()

    def show(annot):
        import wbia.plottool as pt

        pt.imshow(annot.rchip)
        pt.draw_kpts2(annot.kpts)

    def show_dstncvs_mask(annot, title='wd', update=True, **kwargs):
        import wbia.plottool as pt

        pt.imshow(annot.dstncvs_mask * 255.0, update=update, title=title, **kwargs)

    def show_fgweight_mask(annot, title='fg', update=True, **kwargs):
        import wbia.plottool as pt

        pt.imshow(annot.fgweight_mask * 255.0, update=update, title=title, **kwargs)

    def load(annot):
        from vtool import image as gtool
        from vtool import features as feattool

        kpts, vecs = feattool.extract_features(annot.fpath)
        annot.kpts = kpts
        annot.vecs = vecs
        annot.rchip = gtool.imread(annot.fpath)
        annot.dstncvs = compute_distinctivness([annot.vecs], annot.species)[0]
        annot.fgweights = compute_forgroundness(annot.fpath, annot.kpts, annot.species)
        annot.chipshape = annot.rchip.shape
        annot.dlen_sqrd = annot.chipshape[0] ** 2 + annot.chipshape[1] ** 2

    def lazy_compute(annot):
        if annot.dstncvs_mask is None:
            annot.compute_dstncvs_mask()
        if annot.fgweight_mask is None:
            annot.compute_fgweight_mask()

    def compute_fgweight_mask(annot):
        keys = ['kpts', 'chipshape', 'fgweights']
        kpts, chipshape, fgweights = ut.dict_take(annot.__dict__, keys)
        chipsize = chipshape[0:2][::-1]
        fgweight_mask = coverage_kpts.make_kpts_coverage_mask(
            kpts, chipsize, fgweights, mode='max', resize=True, return_patch=False
        )
        annot.fgweight_mask = fgweight_mask

    def compute_dstncvs_mask(annot):
        keys = ['kpts', 'chipshape', 'dstncvs']
        kpts, chipshape, dstncvs = ut.dict_take(annot.__dict__, keys)
        chipsize = chipshape[0:2][::-1]
        dstncvs_mask = coverage_kpts.make_kpts_coverage_mask(
            kpts, chipsize, dstncvs, mode='max', resize=True, return_patch=False
        )
        annot.dstncvs_mask = dstncvs_mask

    def baseline_match(annot, annot2):
        cfgdict = {}
        annot1 = annot
        keys = ['kpts', 'vecs']
        kpts1, vecs1 = ut.dict_take(annot1.__dict__, keys)
        kpts2, vecs2 = ut.dict_take(annot2.__dict__, keys)
        dlen_sqrd2 = annot2.dlen_sqrd
        basetup, base_meta = baseline_vsone_ratio_matcher_(
            kpts1, vecs1, kpts2, vecs2, dlen_sqrd2, cfgdict
        )
        (fm_ORIG, fs_ORIG, fm_RAT, fs_RAT, fm_SV, fs_SV, H_RAT) = basetup
        (fm_norm_RAT, fm_norm_SV) = base_meta
        match_ORIG = AnnotMatch(annot1, annot2, fm_ORIG, fs_ORIG, 'ORIG')  # NOQA
        match_RAT = AnnotMatch(annot1, annot2, fm_RAT, fs_RAT, 'RAT', fm_norm_RAT)  # NOQA
        match_SV = AnnotMatch(annot1, annot2, fm_SV, fs_SV, 'SV', fm_norm_SV)
        match_SV.H = H_RAT
        return match_ORIG, match_RAT, match_SV

    def constrained_match(annot, match_SV):
        cfgdict = {}
        annot1 = match_SV.annot1
        assert annot1 is annot
        annot2 = match_SV.annot2
        keys = ['kpts', 'vecs']
        kpts1, vecs1 = ut.dict_take(annot1.__dict__, keys)
        kpts2, vecs2 = ut.dict_take(annot2.__dict__, keys)
        dlen_sqrd2 = annot2.dlen_sqrd
        H_RAT = match_SV.H
        nexttup, next_meta = spatially_constrianed_matcher_(
            kpts1, vecs1, kpts2, vecs2, dlen_sqrd2, H_RAT, cfgdict
        )
        (fm_SC, fs_SC, fm_SCR, fs_SCR, fm_SCRSV, fs_SCRSV, H_SCR) = nexttup
        (fm_norm_SC, fm_norm_SCR, fm_norm_SCRSV) = next_meta
        match_SC = AnnotMatch(annot1, annot2, fm_SC, fs_SC, 'SC', fm_norm_SC)  # NOQA
        match_SCR = AnnotMatch(annot1, annot2, fm_SCR, fs_SCR, 'SCR', fm_norm_SCR)  # NOQA
        match_SCRSV = AnnotMatch(
            annot1, annot2, fm_SCRSV, fs_SCRSV, 'SCRSV', fm_norm_SCRSV
        )
        match_SCRSV.H = H_SCR
        return match_SC, match_SCR, match_SCRSV


@six.add_metaclass(ut.ReloadingMetaclass)
class AnnotMatch(object):
    r"""

    Example1:
        >>> from vtool.constrained_matching import *  # NOQA
        >>> fname1, fname2 = 'easy1.png', 'easy2.png'
        >>> fpath1 = ut.grab_test_imgpath(fname1)
        >>> fpath2 = ut.grab_test_imgpath(fname2)
        >>> annot1, annot2 = Annot(fpath1), Annot(fpath2)
        >>> match_ORIG, match_RAT, match_SV = annot1.baseline_match(annot2)
        >>> match = match_SV
        >>> match_SC, match_SCR, match_SCRSV = annot1.constrained_match(match_SV)
        >>> match = match_SCR
        >>> # ___
        >>> match_list = [match_ORIG, match_RAT, match_SV, match_SC, match_SCR, match_SCRSV]
        >>> # false match
        >>> fname3 = 'hard3.png'
        >>> fpath3 = ut.grab_test_imgpath(fname3)
        >>> annot3 = Annot(fpath3)
        >>> match_tn_list = []
        >>> match_tn_list.extend(annot1.baseline_match(annot3))
        >>> match_SV_fn = match_tn_list[-1]
        >>> match_tn_list.extend(annot1.constrained_match(match_SV_fn))
        >>> # ___
        >>> print('___________')
        >>> for match in match_list:
        >>>    match.print_scores()
        >>> print('___________')
        >>> for match_tn in match_tn_list:
        >>>    match_tn.print_scores()
        >>> print('___________')
        >>> for match, match_tn in zip(match_list, match_tn_list):
        >>>    match.print_score_diffs(match_tn)

    Ignore::
        match.show_matches(fnum=1, update=True)

        match.show_normalizers(fnum=2, update=True)
    """

    def __init__(match, annot1, annot2, fm, fs, key=None, fm_norm=None):
        match.key = key
        match.annot1 = annot1
        match.annot2 = annot2
        match.fm = fm
        match.fs = fs
        match.fm_norm = fm_norm

        # Matching coverage of annot2
        match.coverage_mask2 = None

        # Scalar scores of theis match
        match.num_matches = None
        match.sum_score = None
        match.ave_score = None
        match.weight_ave_score = None
        match.coverage_score = None
        match.weighted_coverage_score = None

    def compute_scores(match):
        match.num_matches = len(match.fm)
        match.sum_score = match.fs.sum()
        match.ave_score = match.fs.sum() / match.fs.shape[0]
        match.weight_ave_score = match.compute_weighte_average_score()
        match.coverage_score = match.coverage_mask2.sum() / np.prod(
            match.coverage_mask2.shape
        )
        match.weighted_coverage_score = match.compute_weighted_coverage_score()

    def compute_weighte_average_score(match):
        """ old scoring measure """
        import vtool as vt

        # Get distinctivness and forground of matching points
        fx1_list, fx2_list = match.fm.T
        annot1 = match.annot1
        annot2 = match.annot2
        dstncvs1 = annot1.dstncvs.take(fx1_list)
        dstncvs2 = annot2.dstncvs.take(fx2_list)
        fgweight1 = annot1.fgweights.take(fx1_list)
        fgweight2 = annot2.fgweights.take(fx2_list)
        dstncvs = np.sqrt(dstncvs1 * dstncvs2)
        fgweight = np.sqrt(fgweight1 * fgweight2)
        fsv = np.vstack((match.fs, dstncvs, fgweight)).T
        fs_new = vt.weighted_average_scoring(fsv, [0], [1, 2])
        weight_ave_score = fs_new.sum()
        return weight_ave_score

    def lazy_compute(match):
        match.annot2.lazy_compute()
        if match.coverage_mask2 is None:
            match.compute_coverage_mask()
        match.compute_scores()

    def compute_weighted_coverage_score(match):
        weight_mask = np.sqrt(match.annot2.dstncvs_mask * match.annot2.fgweight_mask)
        conerage_score = match.coverage_mask2.sum() / weight_mask.sum()
        return conerage_score

    def compute_coverage_mask(match):
        """ compute matching coverage of annot """
        fm = match.fm
        fs = match.fs
        kpts2 = match.annot2.kpts
        chipshape2 = match.annot2.chipshape
        chipsize2 = chipshape2[0:2][::-1]
        kpts2_m = kpts2.take(fm.T[1], axis=0)
        coverage_mask2 = coverage_kpts.make_kpts_coverage_mask(
            kpts2_m, chipsize2, fs, mode='max', resize=True, return_patch=False
        )
        match.coverage_mask2 = coverage_mask2

    # --- INFO ---

    def print_scores(match):
        match.lazy_compute()
        score_keys = [
            'num_matches',
            'sum_score',
            'ave_score',
            'weight_ave_score',
            'coverage_score',
            'weighted_coverage_score',
        ]
        msglist = []
        for key in score_keys:
            msglist.append(' * %s = %6.2f' % (key, match.__dict__[key]))
        msglist_aligned = ut.align_lines(msglist, '=')
        msg = '\n'.join(msglist_aligned)
        print('key = %r' % (match.key,))
        print(msg)

    def print_score_diffs(match, match_tn):
        score_keys = [
            'num_matches',
            'sum_score',
            'ave_score',
            'weight_ave_score',
            'coverage_score',
            'weighted_coverage_score',
        ]
        msglist = [' * <key> =   <tp>,   <tn>, <diff>, <factor>']
        for key in score_keys:
            score = match.__dict__[key]
            score_tn = match_tn.__dict__[key]
            score_diff = score - score_tn
            score_factor = score / score_tn
            msglist.append(
                ' * %s = %6.2f, %6.2f, %6.2f, %6.2f'
                % (key, score, score_tn, score_diff, score_factor)
            )
        msglist_aligned = ut.align_lines(msglist, '=')
        msg = '\n'.join(msglist_aligned)
        print('key = %r' % (match.key,))
        print(msg)

    def show_matches(match, fnum=None, pnum=None, update=True):
        import wbia.plottool as pt
        from wbia.plottool import plot_helpers as ph

        # hack keys out of namespace
        keys = ['rchip', 'kpts']
        rchip1, kpts1 = ut.dict_take(match.annot1.__dict__, keys)
        rchip2, kpts2 = ut.dict_take(match.annot2.__dict__, keys)
        fs, fm = match.fs, match.fm
        cmap = 'hot'
        draw_lines = True
        if fnum is None:
            fnum = pt.next_fnum()
        pt.figure(fnum=fnum, pnum=pnum)
        # doclf=True, docla=True)
        ax, xywh1, xywh2 = pt.show_chipmatch2(
            rchip1,
            rchip2,
            kpts1,
            kpts2,
            fm=fm,
            fs=fs,
            fnum=fnum,
            cmap=cmap,
            draw_lines=draw_lines,
        )
        ph.set_plotdat(ax, 'viztype', 'matches')
        ph.set_plotdat(ax, 'key', match.key)
        title = match.key + '\n num=%d, sum=%.2f' % (len(fm), sum(fs))
        pt.set_title(title)
        if update:
            pt.update()
        return ax, xywh1, xywh2

    def show_normalizers(match, fnum=None, pnum=None, update=True):
        import wbia.plottool as pt
        from wbia.plottool import plot_helpers as ph

        # hack keys out of namespace
        keys = ['rchip', 'kpts']
        rchip1, kpts1 = ut.dict_take(match.annot1.__dict__, keys)
        rchip2, kpts2 = ut.dict_take(match.annot2.__dict__, keys)
        fs, fm = match.fs, match.fm_norm
        cmap = 'cool'
        draw_lines = True
        if fnum is None:
            fnum = pt.next_fnum()
        pt.figure(fnum=fnum, pnum=pnum)
        # doclf=True, docla=True)
        ax, xywh1, xywh2 = pt.show_chipmatch2(
            rchip1,
            rchip2,
            kpts1,
            kpts2,
            fm=fm,
            fs=fs,
            fnum=fnum,
            cmap=cmap,
            draw_lines=draw_lines,
        )
        ph.set_plotdat(ax, 'viztype', 'matches')
        ph.set_plotdat(ax, 'key', match.key)
        title = match.key + '\n num=%d, sum=%.2f' % (len(fm), sum(fs))
        pt.set_title(title)
        if update:
            pt.update()
        return ax, xywh1, xywh2


def testdata_matcher(fname1='easy1.png', fname2='easy2.png'):
    """"
    fname1 = 'easy1.png'
    fname2 = 'hard3.png'

    annot1 = Annot(fpath1)
    annot2 = Annot(fpath2)
    """
    import utool as ut
    from vtool import image as gtool
    from vtool import features as feattool

    fpath1 = ut.grab_test_imgpath(fname1)
    fpath2 = ut.grab_test_imgpath(fname2)
    kpts1, vecs1 = feattool.extract_features(fpath1)
    kpts2, vecs2 = feattool.extract_features(fpath2)
    rchip1 = gtool.imread(fpath1)
    rchip2 = gtool.imread(fpath2)
    # chip1_shape = vt.gtool.open_image_size(fpath1)
    chip2_shape = gtool.open_image_size(fpath2)
    dlen_sqrd2 = chip2_shape[0] ** 2 + chip2_shape[1] ** 2
    testtup = (rchip1, rchip2, kpts1, vecs1, kpts2, vecs2, dlen_sqrd2)

    return testtup


if __name__ == '__main__':
    """
    CommandLine:
        python -m vtool.constrained_matching
        python -m vtool.constrained_matching --allexamples
        python -m vtool.constrained_matching --allexamples --noface --nosrc
    """
    import multiprocessing

    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA

    ut.doctest_funcs()


from __future__ import absolute_import, division, print_function
import utool as ut
import six  # NOQA
import numpy as np  # NOQA
from vtool import keypoint as ktool  # NOQA
from vtool import spatial_verification as sver  # NOQA
from vtool import constrained_matching

"""
Todo tomorrow:

add coverage as option to IBEIS
add spatially constrained matching as option to IBEIS

"""


def param_interaction():
    r"""
    CommandLine:
        python -m vtool.test_constrained_matching --test-param_interaction

    Notes:
        python -m vtool.test_constrained_matching --test-param_interaction
        setparam normalizer_mode=nearby
        setparam normalizer_mode=far
        setparam ratio_thresh=.625
        setparam ratio_thresh=.5

        setparam ratio_thresh2=.625
        normalizer_mode=plus

    Example:
        >>> # DISABLE_DOCTEST
        >>> from vtool.test_constrained_matching import *  # NOQA
        >>> # build test data
        >>> # execute function
        >>> testtup = param_interaction()
        >>> # verify results
        >>> result = str(testtup)
        >>> print(result)
    """
    import wbia.plottool as pt

    USE_IBEIS = False and ut.is_developer()
    if USE_IBEIS:
        from wbia.algo.hots import devcases

        index = 2
        fpath1, fpath2, fpath3 = devcases.get_dev_test_fpaths(index)
        testtup1 = testdata_matcher(fpath1, fpath2)
        testtup2 = testdata_matcher(fpath1, fpath3)
    else:
        testtup1 = testdata_matcher('easy1.png', 'easy2.png')
        testtup2 = testdata_matcher('easy1.png', 'hard3.png')
    testtup_list = [testtup1, testtup2]
    simp_list = [SimpleMatcher(testtup) for testtup in testtup_list]
    varied_dict = dict(
        [
            ('sver_xy_thresh', 0.1),
            ('ratio_thresh', 0.625),
            ('search_K', 7),
            ('ratio_thresh2', 0.625),
            ('sver_xy_thresh2', 0.01),
            ('normalizer_mode', ['nearby', 'far', 'plus'][1]),
            ('match_xy_thresh', 0.1),
        ]
    )
    cfgdict_list = ut.all_dict_combinations(varied_dict)
    tried_configs = []

    # DEFINE CUSTOM INTRACTIONS
    custom_actions, valid_vizmodes, viz_index_, offset_fnum_ = make_custom_interactions(
        simp_list
    )
    # /DEFINE CUSTOM INTRACTIONS

    for cfgdict in ut.InteractiveIter(
        cfgdict_list,
        # default_action='reload',
        custom_actions=custom_actions,
        wraparound=True,
    ):
        for simp in simp_list:
            simp.run_matching(cfgdict=cfgdict)
        vizkey = valid_vizmodes[viz_index_[0]].replace('visualize_', '')
        print('vizkey = %r' % (vizkey,))
        for fnum_, simp in enumerate(simp_list):
            fnum = fnum_ + offset_fnum_[0]
            simp.visualize(vizkey, fnum=fnum)
        tried_configs.append(cfgdict.copy())
        print('Current Config = ')
        print(ub.repr2(cfgdict))
        pt.present()
        pt.update()


def make_custom_interactions(simp_list):
    valid_vizmodes = ut.filter_startswith(dir(SimpleMatcher), 'visualize_')
    viz_index_ = [valid_vizmodes.index('visualize_matches')]

    def toggle_vizmode(iiter, actionkey, value, viz_index_=viz_index_):
        viz_index_[0] = (viz_index_[0] + 1) % len(valid_vizmodes)
        print('toggling')

    def set_param(iiter, actionkey, value, viz_index_=viz_index_):
        """
        value = 'search_K=3'
        """
        paramkey, paramval = value.split('=')
        print('parsing value=%r' % (value,))

        def strip_quotes(str_):
            dq = ut.DOUBLE_QUOTE
            sq = ut.SINGLE_QUOTE
            return str_.strip(dq).strip(sq).strip(dq)

        # Sanatize
        paramkey = strip_quotes(paramkey.strip())
        paramval = ut.smart_cast2(strip_quotes(paramval.strip()))
        print('setting cfgdict[%r]=%r' % (paramkey, paramval))
        iiter.iterable[iiter.index][paramkey] = paramval

    offset_fnum_ = [0]

    def offset_fnum(iiter, actionkey, value, offset_fnum_=offset_fnum_):
        offset_fnum_[0] += len(simp_list)

    custom_actions = [
        (
            'toggle',
            ['t'],
            'toggles between ' + ut.conj_phrase(valid_vizmodes, 'and'),
            toggle_vizmode,
        ),
        (
            'offset_fnum',
            ['offset_fnum', 'o'],
            'offset the figure number (keeps old figures)',
            offset_fnum,
        ),
        (
            'set_param',
            ['setparam', 's'],
            'sets a config param using key=val format.  eg: setparam ratio_thresh=.1',
            set_param,
        ),
    ]
    return custom_actions, valid_vizmodes, viz_index_, offset_fnum_


def testdata_matcher(fname1='easy1.png', fname2='easy2.png'):
    """"
    fname1 = 'easy1.png'
    fname2 = 'hard3.png'

    python -m vtool.test_constrained_matching --test-visualize_matches --show

    Args:
        fname1 (str): (default = 'easy1.png')
        fname2 (str): (default = 'easy2.png')

    Returns:
        ?: testtup

    CommandLine:
        python -m vtool.test_constrained_matching --test-testdata_matcher

    Example:
        >>> # DISABLE_DOCTEST
        >>> from vtool.test_constrained_matching import *  # NOQA
        >>> fname1 = 'easy1.png'
        >>> fname2 = 'easy2.png'
        >>> testtup = testdata_matcher(fname1, fname2)
        >>> result = ('testtup = %s' % (str(testtup),))
        >>> print(result)
    """
    import utool as ut

    # import vtool as vt
    from vtool import image as gtool
    from vtool import features as feattool

    fpath1 = ut.grab_test_imgpath(fname1)
    fpath2 = ut.grab_test_imgpath(fname2)
    featkw = dict(rotation_invariance=True)
    kpts1, vecs1 = feattool.extract_features(fpath1, **featkw)
    kpts2, vecs2 = feattool.extract_features(fpath2, **featkw)
    # if featkw['rotation_invariance']:
    #    print('ori stats 1 ' + ut.get_stats_str(vt.get_oris(kpts2)))
    #    print('ori stats 2 ' + ut.get_stats_str(vt.get_oris(kpts1)))
    rchip1 = gtool.imread(fpath1)
    rchip2 = gtool.imread(fpath2)
    # chip1_shape = vt.gtool.open_image_size(fpath1)
    chip2_shape = gtool.open_image_size(fpath2)
    dlen_sqrd2 = chip2_shape[0] ** 2 + chip2_shape[1]
    testtup = (rchip1, rchip2, kpts1, vecs1, kpts2, vecs2, dlen_sqrd2)
    return testtup


class SimpleMatcher(object):
    def __init__(simp, testtup):
        simp.testtup = None
        simp.basetup = None
        simp.nexttup = None
        if testtup is not None:
            simp.load_data(testtup)

    def load_data(simp, testtup):
        simp.testtup = testtup

    def run_matching(simp, testtup=None, cfgdict={}):
        if testtup is None:
            testtup = simp.testtup
        basetup, base_meta = constrained_matching.baseline_vsone_ratio_matcher(
            testtup, cfgdict
        )
        nexttup, next_meta = constrained_matching.spatially_constrianed_matcher(
            testtup, basetup, cfgdict
        )
        simp.nexttup = nexttup
        simp.basetup = basetup
        simp.testtup = testtup
        simp.base_meta = base_meta
        simp.next_meta = next_meta

    def setstate_testdata(simp):
        testtup = testdata_matcher()
        simp.run_matching(testtup)

    def visualize(simp, key, **kwargs):
        visualize_method = getattr(simp, 'visualize_' + key)
        return visualize_method(**kwargs)

    def start_new_viz(simp, nRows, nCols, fnum=None):
        import wbia.plottool as pt

        rchip1, rchip2, kpts1, vecs1, kpts2, vecs2, dlen_sqrd2 = simp.testtup
        fm_ORIG, fs_ORIG, fm_RAT, fs_RAT, fm_SV, fs_SV, H_RAT = simp.basetup
        fm_SC, fs_SC, fm_SCR, fs_SCR, fm_SCRSV, fs_SCRSV, H_SCR = simp.nexttup
        fm_norm_RAT, fm_norm_SV = simp.base_meta
        fm_norm_SC, fm_norm_SCR, fm_norm_SVSCR = simp.next_meta

        locals_ = ut.delete_dict_keys(locals(), ['title'])

        keytitle_tups = [
            ('ORIG', 'initial neighbors'),
            ('RAT', 'ratio filtered'),
            ('SV', 'ratio filtered + SV'),
            ('SC', 'spatially constrained'),
            ('SCR', 'spatially constrained + ratio'),
            ('SCRSV', 'spatially constrained + SV'),
        ]
        keytitle_dict = dict(keytitle_tups)
        key_list = ut.get_list_column(keytitle_tups, 0)
        matchtup_dict = {
            key: (locals_['fm_' + key], locals_['fs_' + key]) for key in key_list
        }
        normtup_dict = {key: locals_.get('fm_norm_' + key, None) for key in key_list}

        next_pnum = pt.make_pnum_nextgen(nRows=nRows, nCols=nCols)
        if fnum is None:
            fnum = pt.next_fnum()
        INTERACTIVE = True
        if INTERACTIVE:
            from wbia.plottool import interact_helpers as ih

            fig = ih.begin_interaction('qres', fnum)
            ih.connect_callback(fig, 'button_press_event', on_single_match_clicked)
        else:
            pt.figure(fnum=fnum, doclf=True, docla=True)

        def show_matches_(key, **kwargs):
            assert key in key_list, 'unknown key=%r' % (key,)
            showkw = locals_.copy()
            pnum = next_pnum()
            showkw['pnum'] = pnum
            showkw['fnum'] = fnum
            showkw.update(kwargs)
            _fm, _fs = matchtup_dict[key]
            title = keytitle_dict[key]
            if kwargs.get('coverage'):
                from vtool import coverage_kpts

                kpts2, rchip2 = ut.dict_get(locals_, ('kpts2', 'rchip2'))
                kpts2_m = kpts2.take(_fm.T[1], axis=0)
                chipshape2 = rchip2.shape
                chipsize2 = chipshape2[0:2][::-1]
                coverage_mask = coverage_kpts.make_kpts_coverage_mask(
                    kpts2_m, chipsize2, fx2_score=_fs, resize=True, return_patch=False
                )
                pt.imshow(coverage_mask * 255, pnum=pnum, fnum=fnum)
            else:
                if kwargs.get('norm', False):
                    _fm = normtup_dict[key]
                    assert _fm is not None, key
                    showkw['cmap'] = 'cool'
                    title += ' normalizers'
                show_matches(_fm, _fs, title=title, key=key, **showkw)

        # state hack
        # show_matches_.next_pnum = next_pnum
        return show_matches_

    def visualize_matches(simp, **kwargs):
        r"""
        CommandLine:
            python -m vtool.test_constrained_matching --test-visualize_matches --show

        Example:
            >>> # DISABLE_DOCTEST
            >>> from vtool.test_constrained_matching import *  # NOQA
            >>> import wbia.plottool as pt
            >>> simp = SimpleMatcher(testdata_matcher())
            >>> simp.run_matching()
            >>> result = simp.visualize_matches()
            >>> pt.show_if_requested()
        """
        nRows = 2
        nCols = 3
        show_matches_ = simp.start_new_viz(nRows, nCols, **kwargs)

        show_matches_('ORIG')
        show_matches_('RAT')
        show_matches_('SV')
        show_matches_('SC')
        show_matches_('SCR')
        show_matches_('SCRSV')

    def visualize_normalizers(simp, **kwargs):
        """
        CommandLine:
            python -m vtool.test_constrained_matching --test-visualize_normalizers --show

        Example:
            >>> # DISABLE_DOCTEST
            >>> from vtool.test_constrained_matching import *  # NOQA
            >>> import wbia.plottool as pt
            >>> simp = SimpleMatcher(testdata_matcher())
            >>> simp.run_matching()
            >>> result = simp.visualize_normalizers()
            >>> pt.show_if_requested()
        """
        nRows = 2
        nCols = 2
        show_matches_ = simp.start_new_viz(nRows, nCols, **kwargs)

        show_matches_('RAT')
        show_matches_('SCR')

        show_matches_('RAT', norm=True)
        show_matches_('SCR', norm=True)

        # show_matches_(fm_RAT, fs_RAT, title='ratio filtered')
        # show_matches_(fm_SCR, fs_SCR, title='constrained matches')

        # show_matches_(fm_norm_RAT, fs_RAT, title='ratio normalizers', cmap='cool')
        # show_matches_(fm_norm_SCR, fs_SCR, title='constrained normalizers', cmap='cool')

    def visualize_coverage(simp, **kwargs):
        """
        CommandLine:
            python -m vtool.test_constrained_matching --test-visualize_coverage --show

        Example:
            >>> # DISABLE_DOCTEST
            >>> from vtool.test_constrained_matching import *  # NOQA
            >>> import wbia.plottool as pt
            >>> simp = SimpleMatcher(testdata_matcher())
            >>> simp.run_matching()
            >>> result = simp.visualize_coverage()
            >>> pt.show_if_requested()
        """
        nRows = 2
        nCols = 2
        show_matches_ = simp.start_new_viz(nRows, nCols, **kwargs)

        show_matches_('SV', draw_lines=False)
        show_matches_('SCRSV', draw_lines=False)
        show_matches_('SV', coverage=True)
        show_matches_('SCRSV', coverage=True)


def show_matches(
    fm,
    fs,
    fnum=1,
    pnum=None,
    title='',
    key=None,
    simp=None,
    cmap='hot',
    draw_lines=True,
    **locals_
):
    # locals_ = locals()
    import wbia.plottool as pt
    from wbia.plottool import plot_helpers as ph

    # hack keys out of namespace
    keys = 'rchip1, rchip2, kpts1, kpts2'.split(', ')
    rchip1, rchip2, kpts1, kpts2 = ut.dict_take(locals_, keys)
    pt.figure(fnum=fnum, pnum=pnum)
    # doclf=True, docla=True)
    ax, xywh1, xywh2 = pt.show_chipmatch2(
        rchip1,
        rchip2,
        kpts1,
        kpts2,
        fm=fm,
        fs=fs,
        fnum=fnum,
        cmap=cmap,
        draw_lines=draw_lines,
        ori=True,
    )
    ph.set_plotdat(ax, 'viztype', 'matches')
    ph.set_plotdat(ax, 'simp', simp)
    ph.set_plotdat(ax, 'key', key)
    title = title + '\n num=%d, sum=%.2f' % (len(fm), sum(fs))
    pt.set_title(title)
    return ax, xywh1, xywh2
    # pt.set_figtitle(title)
    # if update:
    # pt.iup()


# def ishow_matches(fm, fs, fnum=1, pnum=None, title='', cmap='hot', **locals_):
#    # TODO make things clickable
def on_single_match_clicked(event):
    from wbia.plottool import interact_helpers as ih
    from wbia.plottool import plot_helpers as ph

    """ result interaction mpl event callback slot """
    print('[viz] clicked result')
    if ih.clicked_outside_axis(event):
        pass
    else:
        ax = event.inaxes
        viztype = ph.get_plotdat(ax, 'viztype', '')
        # printDBG(str(event.__dict__))
        # Clicked a specific matches
        if viztype.startswith('matches'):
            # aid2 = ph.get_plotdat(ax, 'aid2', None)
            # Ctrl-Click
            evkey = '' if event.key is None else event.key
            simp = ph.get_plotdat(ax, 'simp', None)
            key = ph.get_plotdat(ax, 'key', None)
            print('evkey = %r' % evkey)
            if evkey.find('control') == 0:
                print('[viz] result control clicked')
                pass
            # Left-Click
            else:
                print(simp)
                print(key)
                print('[viz] result clicked')
                pass
    ph.draw()


def show_example():
    r"""
    CommandLine:
        python -m vtool.test_constrained_matching --test-show_example --show

    Example:
        >>> # DISABLE_DOCTEST
        >>> from vtool.test_constrained_matching import *  # NOQA
        >>> import wbia.plottool as pt
        >>> # build test data
        >>> # execute function
        >>> result = show_example()
        >>> # verify results
        >>> print(result)
        >>> pt.present()
        >>> pt.show_if_requested()
    """
    # ut.util_grabdata.get_valid_test_imgkeys()
    testtup1 = testdata_matcher('easy1.png', 'easy2.png')
    testtup2 = testdata_matcher('easy1.png', 'hard3.png')
    simp1 = SimpleMatcher(testtup1)
    simp2 = SimpleMatcher(testtup2)
    simp1.run_matching()
    simp2.run_matching()
    simp1.visualize_matches()
    simp2.visualize_matches()
    # simp1.visualize_normalizers()
    # simp2.visualize_normalizers()
    # simp1.param_interaction()


if __name__ == '__main__':
    """
    CommandLine:
        python -m vtool.test_constrained_matching
        python -m vtool.test_constrained_matching --allexamples
        python -m vtool.test_constrained_matching --allexamples --noface --nosrc
    """
    import multiprocessing

    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA

    ut.doctest_funcs()


def spatially_constrained_ratio_match(
    flann,
    vecs2,
    kpts1,
    kpts2,
    H,
    chip2_dlen_sqrd,
    match_xy_thresh=1.0,
    scr_ratio_thresh=0.625,
    scr_K=7,
    norm_xy_bounds=(0.0, 1.0),
    fm_dtype=np.int32,
    fs_dtype=np.float32,
):
    """
    performs nearest neighbors, then assigns based on spatial constraints, the
    last step performs a ratio test.

    H - a homography H that maps image1 space into image2 space
    H should map from query to database chip (1 to 2)
    """
    assert H.shape == (3, 3)
    # Find several of image2's features nearest matches in image1
    fx2_to_fx1, fx2_to_dist = normalized_nearest_neighbors(
        flann, vecs2, scr_K, checks=800
    )
    # Then find those which satisfify the constraints
    assigntup = assign_spatially_constrained_matches(
        chip2_dlen_sqrd,
        kpts1,
        kpts2,
        H,
        fx2_to_fx1,
        fx2_to_dist,
        match_xy_thresh,
        norm_xy_bounds=norm_xy_bounds,
    )
    fm, fx1_norm, match_dist, norm_dist = assigntup
    # filter assignments via the ratio test
    scr_tup = ratio_test(
        fm,
        fx1_norm,
        match_dist,
        norm_dist,
        scr_ratio_thresh,
        fm_dtype=fm_dtype,
        fs_dtype=fs_dtype,
    )
    return scr_tup


def ratio_test(
    fm,
    fx1_norm,
    match_dist,
    norm_dist,
    ratio_thresh=0.625,
    fm_dtype=np.int32,
    fs_dtype=np.float32,
):
    r"""
    Lowes ratio test for one-vs-one feature matches.

    Assumes reverse matches (image2 to image1) and returns (image1 to image2)
    matches. Generalized to accept any match or normalizer not just K=1 and K=2.

    Args:
        fx2_to_fx1 (ndarray): nearest neighbor indices (from flann)
        fx2_to_dist (ndarray): nearest neighbor distances (from flann)
        ratio_thresh (float):
        match_col (int or ndarray): column of matching indices
        norm_col (int or ndarray): column of normalizng indices

    Returns:
        tuple: (fm_RAT, fs_RAT, fm_norm_RAT)

    CommandLine:
        python -m vtool.matching --test-ratio_test

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool.matching import *  # NOQA
        >>> fx2_match  = np.array([0, 1, 2, 3, 4, 5], dtype=np.int32)
        >>> fx1_match  = np.array([77, 116, 122, 1075, 530, 45], dtype=np.int32)
        >>> fm = np.vstack((fx1_match, fx2_match)).T
        >>> fx1_norm   = np.array([971, 120, 128, 692, 45, 530], dtype=np.int32)
        >>> match_dist = np.array([ 0.059, 0.021, 0.039, 0.15 , 0.227, 0.216])
        >>> norm_dist  = np.array([ 0.239, 0.241, 0.248, 0.151, 0.244, 0.236])
        >>> ratio_thresh = .625
        >>> ratio_tup = ratio_test(fm, fx1_norm, match_dist, norm_dist, ratio_thresh)
        >>> result = ut.repr3(ratio_tup, precision=3)
        >>> print(result)
        (
            np.array([[ 77,   0],
                      [116,   1],
                      [122,   2]], dtype=np.int32),
            np.array([ 0.753,  0.913,  0.843], dtype=np.float32),
            np.array([[971,   0],
                      [120,   1],
                      [128,   2]], dtype=np.int32),
        )
    """
    fx2_to_ratio = np.divide(match_dist, norm_dist).astype(fs_dtype)
    fx2_to_isvalid = np.less(fx2_to_ratio, ratio_thresh)
    fm_RAT = fm.compress(fx2_to_isvalid, axis=0).astype(fm_dtype)
    fx1_norm_RAT = fx1_norm.compress(fx2_to_isvalid).astype(fm_dtype)
    # Turn the ratio into a score
    fs_RAT = np.subtract(1.0, fx2_to_ratio.compress(fx2_to_isvalid))
    # return normalizer info as well
    fm_norm_RAT = np.vstack((fx1_norm_RAT, fm_RAT.T[1])).T
    ratio_tup = MatchTup3(fm_RAT, fs_RAT, fm_norm_RAT)
    return ratio_tup


def unconstrained_ratio_match(
    flann, vecs2, unc_ratio_thresh=0.625, fm_dtype=np.int32, fs_dtype=np.float32
):
    """ Lowes ratio matching

    from vtool.matching import *  # NOQA
    fs_dtype = rat_kwargs.get('fs_dtype', np.float32)
    fm_dtype = rat_kwargs.get('fm_dtype', np.int32)
    unc_ratio_thresh = rat_kwargs.get('unc_ratio_thresh', .625)

    """
    fx2_to_fx1, fx2_to_dist = normalized_nearest_neighbors(flann, vecs2, K=2, checks=800)
    # ut.embed()
    assigntup = assign_unconstrained_matches(fx2_to_fx1, fx2_to_dist, 1)
    fm, fx1_norm, match_dist, norm_dist = assigntup
    ratio_tup = ratio_test(
        fm,
        fx1_norm,
        match_dist,
        norm_dist,
        unc_ratio_thresh,
        fm_dtype=fm_dtype,
        fs_dtype=fs_dtype,
    )
    return ratio_tup


def assign_spatially_constrained_matches(
    chip2_dlen_sqrd,
    kpts1,
    kpts2,
    H,
    fx2_to_fx1,
    fx2_to_dist,
    match_xy_thresh,
    norm_xy_bounds=(0.0, 1.0),
):
    r"""
    assigns spatially constrained vsone match using results of nearest
    neighbors.

    Args:
        chip2_dlen_sqrd (dict):
        kpts1 (ndarray[float32_t, ndim=2]):  keypoints
        kpts2 (ndarray[float32_t, ndim=2]):  keypoints
        H (ndarray[float64_t, ndim=2]):  homography/perspective matrix that
            maps image1 space into image2 space
        fx2_to_fx1 (ndarray): image2s nearest feature indices in image1
        fx2_to_dist (ndarray):
        match_xy_thresh (float):
        norm_xy_bounds (tuple):

    Returns:
        tuple: assigntup(
            fx2_match, - matching feature indices in image 2
            fx1_match, - matching feature indices in image 1
            fx1_norm,  - normmalizing indices in image 1
            match_dist, - descriptor distances between fx2_match and fx1_match
            norm_dist, - descriptor distances between fx2_match and fx1_norm
            )

    CommandLine:
        python -m vtool.matching assign_spatially_constrained_matches

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool.matching import *  # NOQA
        >>> kpts1 = np.array([[  6.,   4.,   15.84,    4.66,    7.24,    0.  ],
        ...                   [  9.,   3.,   20.09,    5.76,    6.2 ,    0.  ],
        ...                   [  1.,   1.,   12.96,    1.73,    8.77,    0.  ],])
        >>> kpts2 = np.array([[  2.,   1.,   12.11,    0.38,    8.04,    0.  ],
        ...                   [  5.,   1.,   22.4 ,    1.31,    5.04,    0.  ],
        ...                   [  6.,   1.,   19.25,    1.74,    4.72,    0.  ],])
        >>> match_xy_thresh = .37
        >>> chip2_dlen_sqrd = 1400
        >>> norm_xy_bounds = (0.0, 1.0)
        >>> H = np.array([[ 2,  0, 0],
        >>>               [ 0,  1, 0],
        >>>               [ 0,  0, 1]])
        >>> fx2_to_fx1 = np.array([[2, 1, 0],
        >>>                        [0, 1, 2],
        >>>                        [2, 0, 1]], dtype=np.int32)
        >>> fx2_to_dist = np.array([[.40, .80, .85],
        >>>                         [.30, .50, .60],
        >>>                         [.80, .90, .91]], dtype=np.float32)
        >>> # verify results
        >>> assigntup = assign_spatially_constrained_matches(
        >>>     chip2_dlen_sqrd, kpts1, kpts2, H, fx2_to_fx1, fx2_to_dist,
        >>>     match_xy_thresh, norm_xy_bounds)
        >>> fm, fx1_norm, match_dist, norm_dist = assigntup
        >>> result = ub.repr2(assigntup, precision=3, nobr=True)
        >>> print(result)
        np.array([[2, 0],
                  [0, 1],
                  [2, 2]], dtype=np.int32),
        np.array([1, 1, 0], dtype=np.int32),
        np.array([ 0.4,  0.3,  0.8], dtype=np.float32),
        np.array([ 0.8,  0.5,  0.9], dtype=np.float32),
    """
    import vtool as vt

    index_dtype = fx2_to_fx1.dtype
    # Find spatial errors of keypoints under current homography
    # (kpts1 mapped into image2 space)
    fx2_to_xyerr_sqrd = vt.get_match_spatial_squared_error(kpts1, kpts2, H, fx2_to_fx1)
    fx2_to_xyerr = np.sqrt(fx2_to_xyerr_sqrd)
    fx2_to_xyerr_norm = np.divide(fx2_to_xyerr, np.sqrt(chip2_dlen_sqrd))

    # Find matches and normalizers that satisfy spatial constraints
    fx2_to_valid_match = ut.inbounds(fx2_to_xyerr_norm, 0.0, match_xy_thresh, eq=True)
    fx2_to_valid_normalizer = ut.inbounds(fx2_to_xyerr_norm, *norm_xy_bounds, eq=True)
    fx2_to_fx1_match_col = vt.find_first_true_indices(fx2_to_valid_match)
    fx2_to_fx1_norm_col = vt.find_next_true_indices(
        fx2_to_valid_normalizer, fx2_to_fx1_match_col
    )

    assert fx2_to_fx1_match_col != fx2_to_fx1_norm_col, 'normlizers are matches!'

    fx2_to_hasmatch = [pos is not None for pos in fx2_to_fx1_norm_col]
    # IMAGE 2 Matching Features
    fx2_match = np.where(fx2_to_hasmatch)[0].astype(index_dtype)
    match_col_list = np.array(
        ut.take(fx2_to_fx1_match_col, fx2_match), dtype=fx2_match.dtype
    )
    norm_col_list = np.array(
        ut.take(fx2_to_fx1_norm_col, fx2_match), dtype=fx2_match.dtype
    )

    # We now have 2d coordinates into fx2_to_fx1
    # Covnert into 1d coordinates for flat indexing into fx2_to_fx1
    _match_index_2d = np.vstack((fx2_match, match_col_list))
    _norm_index_2d = np.vstack((fx2_match, norm_col_list))
    _shape2d = fx2_to_fx1.shape
    match_index_1d = np.ravel_multi_index(_match_index_2d, _shape2d)
    norm_index_1d = np.ravel_multi_index(_norm_index_2d, _shape2d)

    # Find initial matches
    # IMAGE 1 Matching Features
    fx1_match = fx2_to_fx1.take(match_index_1d)
    fx1_norm = fx2_to_fx1.take(norm_index_1d)
    # compute constrained ratio score
    match_dist = fx2_to_dist.take(match_index_1d)
    norm_dist = fx2_to_dist.take(norm_index_1d)

    # package and return
    fm = np.vstack((fx1_match, fx2_match)).T
    assigntup = fm, fx1_norm, match_dist, norm_dist
    return assigntup


def gridsearch_match_operation(matches, op_name, basis):
    import sklearn
    import sklearn.metrics

    y_true = np.array([m.annot1['nid'] == m.annot2['nid'] for m in matches])
    grid = ut.all_dict_combinations(basis)
    auc_list = []
    for cfgdict in ut.ProgIter(grid, lbl='gridsearch', bs=False):
        matches_ = [match.copy() for match in matches]
        y_score = [getattr(m, op_name)(cfgdict=cfgdict).fs.sum() for m in matches_]
        auc = sklearn.metrics.roc_auc_score(y_true, y_score)
        print('cfgdict = %r' % (cfgdict,))
        print('auc = %r' % (auc,))
        auc_list.append(auc)
    print(ut.repr4(ut.sort_dict(ut.dzip(grid, auc_list), 'vals', reverse=True)))
    if len(basis) == 1:
        # interpolate along basis
        pass
