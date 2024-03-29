import numpy as np
import utool as ut
import ubelt as ub
import functools  # NOQA


def safe_vstack(tup, default_shape=(0,), default_dtype=float):
    """ stacks a tuple even if it is empty """
    try:
        return np.vstack(tup)
    except ValueError:
        return np.empty(default_shape, dtype=default_dtype)


def pad_vstack(arrs, fill_value=0):
    """ Stacks values and pads arrays with different lengths with zeros """
    total = max(map(len, arrs))
    padded = [np.hstack([a, np.full(total - len(a), fill_value)]) for a in arrs]
    return np.vstack(padded)


def safe_cat(tup, axis=0, default_shape=(0,), default_dtype=float):
    """
    stacks a tuple even if it is empty
    Also deals with numpy bug where cat fails if an element in sequence is empty

    Example:
        >>> # DISABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> import vtool_ibeis as vt
        >>> # test1
        >>> tup = []
        >>> ut.assert_eq(vt.safe_cat(tup, axis=0).shape, (0,))
        >>> # test2
        >>> tup = (np.array([[1, 2, 3]]), np.array([[]]))
        >>> s = vt.safe_cat(tup, axis=0)
        >>> print(ub.hzcat(['s = ', ub.repr2(s)]))
        >>> ut.assert_eq(s.shape, (1, 3))
        >>> # test3
        >>> tup = (np.array([[1, 2, 3]]), np.array([[3, 4, 5]]))
        >>> s = vt.safe_cat(tup, axis=1)
        >>> print(ub.hzcat(['s = ', ub.repr2(s)]))
        >>> ut.assert_eq(s.shape, (1, 6))
        >>> # test3
        >>> tup = (np.array(1), np.array(2), np.array(3))
        >>> s = vt.safe_cat(tup, axis=0)
        >>> print(ub.hzcat(['s = ', ub.repr2(s)]))
        >>> ut.assert_eq(s.shape, (3,))
    """
    if tup is None or len(tup) == 0:
        stack = np.empty(default_shape, dtype=default_dtype)
    else:
        try:
            stack = np.concatenate(tup, axis=axis)
        except ValueError as ex1:
            try:
                # Ensure everything is at least a 1d array
                tup_ = [np.atleast_1d(np.asarray(a)) for a in tup]
                # remove empty parts
                tup_ = [a for a in tup_ if a.size > 0]
                stack = np.concatenate(tup_, axis=axis)
            except ValueError:
                # if axis == 0:
                #     stack = np.hstack(tup)
                # elif axis == 1:
                #     stack = np.vstack(tup)
                # elif axis == 3:
                #     stack = np.dstack(tup)
                # else:
                raise ex1
    return stack
    # try:
    #     return np.concatenate(tup, axis=axis)
    # except ValueError:


def median_abs_dev(arr_list, **kwargs):
    """
    References:
        https://en.wikipedia.org/wiki/Median_absolute_deviation
    """
    return np.median(np.abs(arr_list - np.median(arr_list, **kwargs)), **kwargs)


def argsort_groups(scores_list, reverse=False, rng=np.random, randomize_levels=True):
    """
    Sorts each group normally, but randomizes order of level values.

    TODO: move to vtool_ibeis

    Args:
        scores_list (list):
        reverse (bool): (default = True)
        rng (module):  random number generator(default = numpy.random)

    CommandLine:
        python -m ibeis.init.filter_annots --exec-argsort_groups

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> scores_list = [
        >>>     np.array([np.nan, np.nan], dtype=np.float32),
        >>>     np.array([np.nan, 2], dtype=np.float32),
        >>>     np.array([4, 1, 1], dtype=np.float32),
        >>>     np.array([7, 3, 3, 0, 9, 7, 5, 8], dtype=np.float32),
        >>>     np.array([2, 4], dtype=np.float32),
        >>>     np.array([np.nan, 4, np.nan, 8, np.nan, 9], dtype=np.float32),
        >>> ]
        >>> reverse = True
        >>> rng = np.random.RandomState(0)
        >>> idxs_list = argsort_groups(scores_list, reverse, rng)
        >>> result = 'idxs_list = %s' % (ut.repr4(idxs_list, with_dtype=False),)
        >>> print(result)

    """
    scores_list_ = [np.array(scores, copy=True).astype(float) for scores in scores_list]
    breakers_list = [rng.rand(len(scores)) for scores in scores_list_]
    # replace nan with -inf, or inf randomize order between equal values
    replval = -np.inf if reverse else np.inf
    # Ensure that nans are ordered last
    for scores in scores_list_:
        scores[np.isnan(scores)] = replval
    # The last column is sorted by first with lexsort
    scorebreaker_list = [np.array((breakers, scores))
                         for scores, breakers in zip(scores_list_, breakers_list)]
    if reverse:
        idxs_list = [np.lexsort(scorebreaker)[::-1] for scorebreaker in  scorebreaker_list]
    else:
        idxs_list = [np.lexsort(scorebreaker) for scorebreaker in  scorebreaker_list]
    return idxs_list


def check_sift_validity(sift_uint8, lbl=None, verbose=ut.NOT_QUIET):
    """
    checks if a SIFT descriptor is valid
    """
    if lbl is None:
        lbl = ut.get_varname_from_stack(sift_uint8, N=1)
    print('[checksift] Checking valididty of %d SIFT descriptors. lbl=%s' % (
        sift_uint8.shape[0], lbl))
    is_correct_shape = len(sift_uint8.shape) == 2 and sift_uint8.shape[1] == 128
    is_correct_dtype = sift_uint8.dtype == np.uint8
    if not is_correct_shape:
        print('[checksift]  * incorrect shape = %r' % (sift_uint8.shape,))
    elif verbose:
        print('[checksift]  * correct shape = %r' % (sift_uint8.shape,))

    if not is_correct_dtype:
        print('[checksift]  * incorrect dtype = %r' % (sift_uint8.dtype,))
    elif verbose:
        print('[checksift]  * correct dtype = %r' % (sift_uint8.dtype,))

    num_sifts = sift_uint8.shape[0]
    sift_float01 = sift_uint8 / 512.0

    # Check L2 norm
    sift_norm = np.linalg.norm(sift_float01, axis=1)
    is_normal = np.isclose(sift_norm, 1.0, atol=.04)
    bad_locs_norm = np.where(np.logical_not(is_normal))[0]
    if len(bad_locs_norm) > 0:
        print('[checksift]  * bad norm   = %4d/%d' % (len(bad_locs_norm), num_sifts))
    else:
        print('[checksift]  * correctly normalized')

    # Check less than thresh=.2
    # This check actually is not valid because the SIFT descriptors is
    # normalized after it is thresholded
    #bad_locs_thresh = np.where((sift_float01 > .2).sum(axis=1))[0]
    #print('[checksift]  * bad thresh = %4d/%d' % (len(bad_locs_thresh), num_sifts))
    #if len(bad_locs_thresh) > 0:
    #    above_thresh = sift_float01[(sift_float01 > .2)]
    #    print('[checksift]  * components under thresh = %d' % (sift_float01 <= 2).sum())
    #    print('[checksift]  * components above thresh stats = ' +
    #    ut.get_stats_str(above_thresh, precision=2))

    isok = len(bad_locs_norm) == 0 and is_correct_shape and is_correct_dtype
    if not isok:
        print('[checksift] ERROR. SIFT CHECK FAILED')
    return isok


def get_crop_slices(isfill):
    fill_colxs = [np.where(row)[0] for row in isfill]
    fill_rowxs = [np.where(col)[0] for col in isfill.T]
    nRows, nCols = isfill.shape[0:2]

    filled_columns = intersect1d_reduce(fill_colxs)
    filled_rows = intersect1d_reduce(fill_rowxs)
    consec_rows_list = ut.group_consecutives(filled_rows)
    consec_cols_list = ut.group_consecutives(filled_columns)

    def get_consec_endpoint(consec_index_list, endpoint):
        """
        consec_index_list = consec_cols_list
        endpoint = 0
        """
        for consec_index in consec_index_list:
            if np.any(np.array(consec_index) == endpoint):
                return consec_index

    def get_min_consec_endpoint(consec_rows_list, endpoint):
        consec_index = get_consec_endpoint(consec_rows_list, endpoint)
        if consec_index is None:
            return endpoint
        return max(consec_index)

    def get_max_consec_endpoint(consec_rows_list, endpoint):
        consec_index = get_consec_endpoint(consec_rows_list, endpoint)
        if consec_index is None:
            return endpoint + 1
        return min(consec_index)

    consec_rows_top    = get_min_consec_endpoint(consec_rows_list, 0)
    consec_rows_bottom = get_max_consec_endpoint(consec_rows_list, nRows - 1)
    remove_cols_left   = get_min_consec_endpoint(consec_cols_list, 0)
    remove_cols_right  = get_max_consec_endpoint(consec_cols_list, nCols - 1)
    rowslice = slice(consec_rows_top, consec_rows_bottom)
    colslice = slice(remove_cols_left, remove_cols_right)
    return rowslice, colslice


def get_undirected_edge_ids(directed_edges):
    r"""
    Args:
        directed_edges (ndarray[ndims=2]):

    Returns:
        list: edgeid_list

    CommandLine:
        python -m vtool_ibeis.other --exec-get_undirected_edge_ids

    Example:
        >>> # DISABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> directed_edges = np.array([[1, 2], [2, 1], [2, 3], [3, 1], [1, 1], [2, 3], [3, 2]])
        >>> edgeid_list = get_undirected_edge_ids(directed_edges)
        >>> result = ('edgeid_list = %s' % (ub.repr2(edgeid_list),))
        >>> print(result)
        edgeid_list = [0 0 1 2 3 1 1]
    """
    #import vtool_ibeis as vt
    undirected_edges = to_undirected_edges(directed_edges)
    edgeid_list = compute_unique_data_ids(undirected_edges)
    return edgeid_list


def to_undirected_edges(directed_edges, upper=False):
    assert len(directed_edges.shape) == 2 and directed_edges.shape[1] == 2
    #flipped = qaid_arr < daid_arr
    if upper:
        flipped = directed_edges.T[0] > directed_edges.T[1]
    else:
        flipped = directed_edges.T[0] < directed_edges.T[1]
    # standardize edge order
    edges_dupl = directed_edges.copy()
    edges_dupl[flipped, 0:2] = edges_dupl[flipped, 0:2][:, ::-1]
    undirected_edges = edges_dupl
    return undirected_edges


def find_best_undirected_edge_indexes(directed_edges, score_arr=None):
    r"""
    Args:
        directed_edges (ndarray[ndims=2]):
        score_arr (ndarray):

    Returns:
        list: unique_edge_xs

    CommandLine:
        python -m vtool_ibeis.other --test-find_best_undirected_edge_indexes

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> directed_edges = np.array([[1, 2], [2, 1], [2, 3], [3, 1], [1, 1], [2, 3], [3, 2]])
        >>> score_arr = np.array([1, 1, 1, 1, 1, 1, 2])
        >>> unique_edge_xs = find_best_undirected_edge_indexes(directed_edges, score_arr)
        >>> result = str(unique_edge_xs)
        >>> print(result)
        [0 3 4 6]

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> directed_edges = np.array([[1, 2], [2, 1], [2, 3], [3, 1], [1, 1], [2, 3], [3, 2]])
        >>> score_arr = None
        >>> unique_edge_xs = find_best_undirected_edge_indexes(directed_edges, score_arr)
        >>> result = str(unique_edge_xs)
        >>> print(result)
        [0 2 3 4]
    """
    import vtool_ibeis as vt
    #assert len(directed_edges.shape) == 2 and directed_edges.shape[1] == 2
    ##flipped = qaid_arr < daid_arr
    #flipped = directed_edges.T[0] < directed_edges.T[1]
    ## standardize edge order
    #edges_dupl = directed_edges.copy()
    #edges_dupl[flipped, 0:2] = edges_dupl[flipped, 0:2][:, ::-1]
    #edgeid_list = vt.compute_unique_data_ids(edges_dupl)
    edgeid_list = get_undirected_edge_ids(directed_edges)
    unique_edgeids, groupxs = vt.group_indices(edgeid_list)
    # if there is more than one edge in a group take the one with the highest score
    if score_arr is None:
        unique_edge_xs_list = [groupx[0] for groupx in groupxs]
    else:
        assert len(score_arr) == len(directed_edges)
        score_groups = vt.apply_grouping(score_arr, groupxs)
        score_argmaxs = [score_group.argmax() for score_group in score_groups]
        unique_edge_xs_list = [
            groupx[argmax] for groupx, argmax in zip(groupxs, score_argmaxs)
        ]
    unique_edge_xs = np.array(sorted(unique_edge_xs_list), dtype=np.int32)
    return unique_edge_xs


def argsort_records(arrays, reverse=False):
    r"""
    Sorts arrays that form records.
    Same as lexsort(arrays[::-1]) --- ie. rows are reversed.

    Args:
        arrays (ndarray): array of records
        reverse (bool): (default = False)

    Returns:
        ndarray: sortx - sorted indicies

    CommandLine:
        python -m vtool_ibeis.other --exec-argsort_records

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> arrays = np.array([
        >>>     [1, 1, 1, 2, 2, 2, 3, 4, 5],
        >>>     [2, 0, 2, 6, 4, 3, 2, 5, 6],
        >>>     [1, 1, 0, 2, 3, 4, 5, 6, 7],
        >>> ],)
        >>> reverse = False
        >>> sortx = argsort_records(arrays, reverse)
        >>> result = ('sortx = %s' % (str(sortx),))
        >>> print('lxsrt = %s' % (np.lexsort(arrays[::-1]),))
        >>> print(result)
        sortx = [1 2 0 5 4 3 6 7 8]
    """
    sorting_records = np.rec.fromarrays(arrays)
    sort_stride = (-reverse * 2) + 1
    sortx = sorting_records.argsort()[::sort_stride]
    return sortx


def unique_rows(arr, directed=True):
    """
    Order or columns does not matter if directed = False
    """
    if directed:
        idx_list = compute_unique_data_ids(arr)
    else:
        idx_list = get_undirected_edge_ids(arr)
    _, unique_rowx = np.unique(idx_list, return_index=True)
    unique_arr = arr.take(unique_rowx, axis=0)
    return unique_arr


def compute_ndarray_unique_rowids_unsafe(arr):
    """
    arr = np.random.randint(2, size=(10000, 10))
    vt.compute_unique_data_ids_(list(map(tuple, arr)))
    len(vt.compute_unique_data_ids_(list(map(tuple, arr))))
    len(np.unique(vt.compute_unique_data_ids_(list(map(tuple, arr)))))

    %timeit vt.compute_unique_data_ids_(list(map(tuple, arr)))
    %timeit compute_ndarray_unique_rowids_unsafe(arr)

    """
    # no checks performed
    void_dtype = np.dtype((np.void, arr.dtype.itemsize * arr.shape[1]))
    #assert arr.flags['C_CONTIGUOUS']
    arr_void_view = arr.view(void_dtype)
    unique, rowids = np.unique(arr_void_view, return_inverse=True)
    return rowids
    #np.ascontiguousarray(arr).data == arr.data
    #assert arr.data == arr_void_view.data


# def nonunique_row_flags(arr):
#     import vtool_ibeis as vt
#     unique_rowx = unique_row_indexes(arr)
#     unique_flags = vt.index_to_boolmask(unique_rowx, len(arr))
#     nonunique_flags = np.logical_not(unique_flags)
#     return nonunique_flags


# def nonunique_row_indexes(arr):
#     """ rows that are not unique (does not include the first instance of each pattern)

#     Args:
#         arr (ndarray): 2d array

#     Returns:
#         ndarray: nonunique_rowx

#     SeeAlso:
#         unique_row_indexes
#         nonunique_row_flags

#     CommandLine:
#         python -m vtool_ibeis.other --test-unique_row_indexes

#     Example:
#         >>> # DISABLE_DOCTEST
#         >>> from vtool_ibeis.other import *  # NOQA
#         >>> arr = np.array([[0, 0], [0, 1], [1, 0], [1, 1], [0, 0], [.534, .432], [.534, .432], [1, 0], [0, 1]])
#         >>> nonunique_rowx = unique_row_indexes(arr)
#         >>> result = ('nonunique_rowx = %s' % (ub.repr2(nonunique_rowx),))
#         >>> print(result)
#         nonunique_rowx = np.array([4, 6, 7, 8], dtype=np.int64)
#     """
#     nonunique_flags = nonunique_row_flags(arr)
#     nonunique_rowx = np.where(nonunique_flags)[0]
#     return nonunique_rowx


def compute_unique_data_ids(data):
    """
    This is actually faster than compute_unique_integer_data_ids it seems

    CommandLine:
        python -m vtool_ibeis.other --test-compute_unique_data_ids

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> data = np.array([[0, 0], [0, 1], [1, 0], [1, 1], [0, 0], [.534, .432], [.534, .432], [1, 0], [0, 1]])
        >>> dataid_list = compute_unique_data_ids(data)
        >>> result = 'dataid_list = ' + ub.repr2(dataid_list, with_dtype=True)
        >>> print(result)
        dataid_list = np.array([0, 1, 2, 3, 0, 4, 4, 2, 1], dtype=np.int32)
    """
    # construct a unique id for every edge
    hashable_rows = [tuple(row_.tolist()) for row_ in data]
    dataid_list = np.array(compute_unique_data_ids_(hashable_rows), dtype=np.int32)
    return dataid_list


def compute_unique_data_ids_(hashable_rows, iddict_=None):
    if iddict_ is None:
        iddict_ = {}
    for row in hashable_rows:
        if row not in iddict_:
            iddict_[row] = len(iddict_)
    dataid_list = list(ub.take(iddict_, hashable_rows))
    return dataid_list


def compute_unique_arr_dataids(arr):
    """ specialized version for speed when arr is an ndarray """
    iddict_ = {}
    hashable_rows = list(map(tuple, arr.tolist()))
    for row in hashable_rows:
        if row not in iddict_:
            iddict_[row] = len(iddict_)
    dataid_list = np.array([iddict_[row] for row in hashable_rows])
    return dataid_list


def compute_unique_integer_data_ids(data):
    r"""
    This is actually slower than compute_unique_data_ids it seems

    Example:
        >>> # DISABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> # build test data
        >>> data = np.array([[0, 0], [0, 1], [1, 1], [0, 0], [0, 0], [0, 1], [1, 1], [0, 0], [9, 0]])
        >>> data = np.random.randint(1000, size=(1000, 2))
        >>> # execute function
        >>> result1 = compute_unique_data_ids(data)
        >>> result2 = compute_unique_integer_data_ids(data)
        >>> # verify results
        >>> print(result)

    %timeit compute_unique_data_ids(data)
    %timeit compute_unique_integer_data_ids(data)
    """
    # construct a unique id for every edge
    ncols = data.shape[1]
    # get the number of decimal places to shift
    exp_step = np.ceil(np.log10(data.max()))
    offsets = [int(10 ** (ix * exp_step)) for ix in reversed(range(0, ncols))]
    dataid_list = np.array([
        sum([
            item * offset
            for item, offset in zip(row, offsets)
        ])
        for row in data])
    return dataid_list


def trytake(list_, index_list):
    return None if list_ is None else list_take_(list_, index_list)


def list_take_(list_, index_list):
    if isinstance(list_, np.ndarray):
        return list_.take(index_list, axis=0)
    else:
        return list(ub.take(list_, index_list))


def compress2(arr, flag_list, axis=None, out=None):
    """
    Wrapper around numpy compress that makes the signature more similar to take
    """
    return np.compress(flag_list, arr, axis=axis, out=out)


def take2(arr, index_list, axis=None, out=None):
    """
    Wrapper around numpy compress that makes the signature more similar to take
    """
    return np.take(arr, index_list, axis=axis, out=out)


def list_compress_(list_, flag_list):
    if isinstance(list_, np.ndarray):
        return list_.compress(flag_list, axis=0)
    else:
        return list(ub.compress(list_, flag_list))


def index_partition(item_list, part1_items):
    """
    returns two lists. The first are the indecies of items in item_list that
    are in part1_items. the second is the indices in item_list that are not
    in part1_items. items in part1_items that are not in item_list are
    ignored

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> item_list = ['dist', 'fg', 'distinctiveness']
        >>> part1_items = ['fg', 'distinctiveness']
        >>> part1_indexes, part2_indexes = index_partition(item_list, part1_items)
        >>> ut.assert_eq(part1_indexes.tolist(), [1, 2])
        >>> ut.assert_eq(part2_indexes.tolist(), [0])
    """
    part1_indexes_ = [
        item_list.index(item)
        for item in part1_items
        if item in item_list
    ]
    part1_indexes = np.array(part1_indexes_)
    part2_indexes = np.setdiff1d(np.arange(len(item_list)), part1_indexes)
    # FIXME: use dtype np.int_
    part1_indexes = part1_indexes.astype(np.int32)
    part2_indexes = part2_indexes.astype(np.int32)
    return part1_indexes, part2_indexes


# def partition_Nones(item_list):
#     """
#     Example:
#         >>> # ENABLE_DOCTEST
#         >>> from vtool_ibeis.other import *  # NOQA
#         >>> item_list = ['foo', None, None, 'bar']
#         >>> part1_indexes, part2_indexes = partition_Nones(item_list)
#     """
#     # part1_indexes_ = ut.list_where(item_list)
#     part1_indexes_ = [index for index, item in enumerate(item_list) if item is not None]
#     part1_indexes = np.array(part1_indexes_)
#     part2_indexes = np.setdiff1d(np.arange(len(item_list)), part1_indexes)
#     return part1_indexes, part2_indexes


def rebuild_partition(part1_vals, part2_vals, part1_indexes, part2_indexes):
    r"""
    Inverts work done by index_partition

    Args:
        part1_vals (list):
        part2_vals (list):
        part1_indexes (dict):
        part2_indexes (dict):

    CommandLine:
        python -m vtool_ibeis.other --test-rebuild_partition

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> item_list = ['dist', 'fg', 'distinctiveness']
        >>> part1_items = ['fg', 'distinctiveness']
        >>> part1_indexes, part2_indexes = index_partition(item_list, part1_items)
        >>> part1_vals = ut.take(item_list, part1_indexes)
        >>> part2_vals = ut.take(item_list, part2_indexes)
        >>> val_list = rebuild_partition(part1_vals, part2_vals, part1_indexes, part2_indexes)
        >>> assert val_list == item_list, 'incorrect inversin'
        >>> print(val_list)
    """
    val_list = [None] * (len(part1_indexes) + len(part2_indexes))
    for idx, val in zip(part1_indexes, part1_vals):
        val_list[idx] = val
    for idx, val in zip(part2_indexes, part2_vals):
        val_list[idx] = val
    return val_list


def weighted_average_scoring(fsv, weight_filtxs, nonweight_filtxs):
    r"""
    does \frac{\sum_i w^f_i * w^d_i * r_i}{\sum_i w^f_i, w^d_i}
    to get a weighed average of ratio scores

    If we normalize the weight part to add to 1 then we can get per-feature
    scores.

    References:
        http://en.wikipedia.org/wiki/Weighted_arithmetic_mean

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> fsv = np.array([
        ...     [ 0.82992172,  1.56136119,  0.66465378],
        ...     [ 0.8000412 ,  2.14719748,  1.        ],
        ...     [ 0.80848503,  2.6816361 ,  1.        ],
        ...     [ 0.86761665,  2.70189977,  1.        ],
        ...     [ 0.8004055 ,  1.58753884,  0.92178345],])
        >>> weight_filtxs = np.array([1, 2], dtype=np.int32)
        >>> nonweight_filtxs = np.array([0], dtype=np.int32)
        >>> new_fs = weighted_average_scoring(fsv, weight_filtxs, nonweight_filtxs)
        >>> result = new_fs
        >>> print(result)

    """
    weight_fs    = fsv.T.take(weight_filtxs, axis=0).T.prod(axis=1)
    nonweight_fs = fsv.T.take(nonweight_filtxs, axis=0).T.prod(axis=1)
    weight_fs_norm01 = weight_fs / weight_fs.sum()
    #weight_fs_norm01[np.isnan(weight_fs_norm01)] = 0.0
    # If weights are nan, fill them with zeros
    weight_fs_norm01 = np.nan_to_num(weight_fs_norm01)
    new_fs = np.multiply(nonweight_fs, weight_fs_norm01)
    return new_fs


def assert_zipcompress(arr_list, flags_list, axis=None):
    num_flags = [len(flags) for flags in flags_list]
    if axis is None:
        num_arrs = [arr.size for arr in arr_list]
    else:
        num_arrs = [arr.shape[axis] for arr in arr_list]
    assert num_flags == num_arrs, 'not able to zipcompress'


def zipcompress_safe(arr_list, flags_list, axis=None):
    arr_list = list(arr_list)
    flags_list = list(flags_list)
    assert_zipcompress(arr_list, flags_list, axis=axis)
    return zipcompress(arr_list, flags_list, axis)


def zipcompress(arr_list, flags_list, axis=None):
    return [np.compress(flags, arr, axis=axis) for arr, flags in zip(arr_list, flags_list)]


def ziptake(arr_list, indices_list, axis=None):
    return [arr.take(indices, axis=axis) for arr, indices in zip(arr_list, indices_list)]


def zipcat(arr1_list, arr2_list, axis=None):
    r"""
    Args:
        arr1_list (list):
        arr2_list (list):
        axis (None): (default = None)

    Returns:
        list:

    CommandLine:
        python -m vtool_ibeis.other --exec-zipcat --show

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> arr1_list = [np.array([0, 0, 0]), np.array([0, 0, 0, 0])]
        >>> arr2_list = [np.array([1, 1, 1]), np.array([1, 1, 1, 1])]
        >>> axis = None
        >>> arr3_list = zipcat(arr1_list, arr2_list, axis)
        >>> arr3_list0 = zipcat(arr1_list, arr2_list, axis=0)
        >>> arr3_list1 = zipcat(arr1_list, arr2_list, axis=1)
        >>> arr3_list2 = zipcat(arr1_list, arr2_list, axis=2)
        >>> print('arr3_list = %s' % (ut.repr3(arr3_list),))
        >>> print('arr3_list0 = %s' % (ut.repr3(arr3_list0),))
        >>> print('arr3_list2 = %s' % (ut.repr3(arr3_list2),))
    """
    import vtool_ibeis as vt
    assert len(arr1_list) == len(arr2_list), 'lists must correspond'
    if axis is None:
        arr1_iter = arr1_list
        arr2_iter = arr2_list
    else:
        arr1_iter = [vt.atleast_nd(arr1, axis + 1) for arr1 in arr1_list]
        arr2_iter = [vt.atleast_nd(arr2, axis + 1) for arr2 in arr2_list]
    arrs_iter = list(zip(arr1_iter, arr2_iter))
    arr3_list = [np.concatenate(arrs, axis=axis) for arrs in arrs_iter]
    return arr3_list


def atleast_nd(arr, n, tofront=False):
    r"""
    View inputs as arrays with at least n dimensions.
    TODO: Commit to numpy

    Args:
        arr (array_like): One array-like object.  Non-array inputs are
            converted to arrays.  Arrays that already have n or more dimensions
            are preserved.
        n (int):
        tofront (bool): if True new dims are added to the front of the array

    CommandLine:
        python -m vtool_ibeis.other --exec-atleast_nd --show

    Returns:
        ndarray :
            An array with ``a.ndim >= n``.  Copies are avoided where possible,
            and views with three or more dimensions are returned.  For example,
            a 1-D array of shape ``(N,)`` becomes a view of shape
            ``(1, N, 1)``, and a 2-D array of shape ``(M, N)`` becomes a view of shape
            ``(M, N, 1)``.

    See Also:
        atleast_1d, atleast_2d, atleast_3d

    Example0:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> n = 2
        >>> arr = np.array([1, 1, 1])
        >>> arr_ = atleast_nd(arr, n)
        >>> result = ub.repr2(arr_.tolist())
        >>> print(result)

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> n = 4
        >>> arr1 = [1, 1, 1]
        >>> arr2 = np.array(0)
        >>> arr3 = np.array([[[[[1]]]]])
        >>> arr1_ = atleast_nd(arr1, n)
        >>> arr2_ = atleast_nd(arr2, n)
        >>> arr3_ = atleast_nd(arr3, n)
        >>> result1 = ub.repr2(arr1_.tolist())
        >>> result2 = ub.repr2(arr2_.tolist())
        >>> result3 = ub.repr2(arr3_.tolist())
        >>> result = '\n'.join([result1, result2, result3])
        >>> print(result)
    """
    arr_ = np.asanyarray(arr)
    ndims = len(arr_.shape)
    if n is not None and ndims <  n:
        # append the required number of dimensions to the end
        if tofront:
            expander = (None,) * (n - ndims) + (Ellipsis,)
        else:
            expander = (Ellipsis,) + (None,) * (n - ndims)
        arr_ = arr_[expander]
    return arr_


def ensure_shape(arr, dimshape):
    """
    Ensures that an array takes a certain shape. The total size of the array
    must not change.

    Args:
        arr (ndarray): array to change the shape of
        dimshape (tuple): desired shape (Nones can be used to broadcast
            dimensions)

    Returns:
        ndarray: arr_ -  the input array, which has been modified inplace.

    CommandLine:
        python -m vtool_ibeis.other ensure_shape

    Doctest:
        >>> from vtool_ibeis.other import *  # NOQA
        >>> arr = np.zeros((7, 7))
        >>> dimshape = (None, None, 3)
        >>> arr2 = ensure_shape(np.array([[1, 2]]), (None, 2))
        >>> assert arr2.shape == (1, 2)
        >>> arr3 = ensure_shape(np.array([]), (None, 2))
        >>> assert arr3.shape == (0, 2)
    """
    if isinstance(dimshape, tuple):
        n = len(dimshape)
    else:
        n = dimshape
        dimshape = None
    arr_ = atleast_nd(arr, n)
    if dimshape is not None:
        newshape = tuple([
            d1 if d2 is None else d2
            for d1, d2 in zip(arr_.shape, dimshape)])
        arr_.shape = newshape
    return arr_


def significant_shape(arr):
    """ find the shape without trailing 1's """
    sig_dim = 0
    for i, dim in enumerate(arr.shape, start=1):
        if dim != 1:
            sig_dim = i
    sig_shape = arr.shape[0:sig_dim]
    return sig_shape


def atleast_shape(arr, dimshape):
    """
    Ensures that an array takes a certain shape. The total size of the array
    must not change.

    Args:
        arr (ndarray): array to change the shape of
        dimshape (tuple): desired shape (Nones can be used to broadcast
            dimensions)

    Returns:
        ndarray: arr_ -  the input array, which has been modified inplace.

    CommandLine:
        python -m vtool_ibeis.other ensure_shape

    Doctest:
        >>> from vtool_ibeis.other import *  # NOQA
        >>> arr = np.zeros((7, 7))
        >>> assert atleast_shape(arr, (1, 1, 3,)).shape == (7, 7, 3)
        >>> assert atleast_shape(arr, (1, 1, 2, 4,)).shape == (7, 7, 2, 4)
        >>> assert atleast_shape(arr, (1, 1,)).shape == (7, 7,)
        >>> assert atleast_shape(arr, (1, 1, 1)).shape == (7, 7, 1)
        >>> assert atleast_shape(np.zeros(()), (1,)).shape == (1,)
        >>> assert atleast_shape(np.zeros(()), tuple()).shape == tuple()
        >>> assert atleast_shape(np.zeros(()), (1, 2, 3,)).shape == (1, 2, 3)
        >>> ut.assert_raises(ValueError, atleast_shape, arr, (2, 2))
        >>> assert atleast_shape(np.zeros((7, 7, 3)), (1, 1, 3)).shape == (7, 7, 3)
        >>> ut.assert_raises(ValueError, atleast_shape, np.zeros((7, 7, 3)), (1, 1, 4))

    """
    n = len(dimshape)
    sig_shape = significant_shape(arr)
    if n < len(sig_shape):
        raise ValueError(
            'len(dimshape)={} must be >= than '
            'len(significant_shape(arr)={})'.format(n, sig_shape))
    arr_ = atleast_nd(arr, n)
    for d1, d2 in zip(arr_.shape, dimshape):
        if d2 > 1 and d1 != 1 and d1 != d2:
            raise ValueError('cannot broadcast {} to {}'.format(
                arr_.shape, dimshape
            ))
    reps = tuple(1 if d2 is None or (d1 == d2) else d2
                 for d1, d2 in zip(arr_.shape, dimshape))
    arr_ = np.tile(arr_, reps)
    return arr_


def atleast_3channels(arr, copy=True):
    r"""
    Ensures that there are 3 channels in the image

    Args:
        arr (ndarray[N, M, ...]): the image
        copy (bool): Always copies if True, if False, then copies only when the
            size of the array must change.

    Returns:
        ndarray: with shape (N, M, C), where C in {3, 4}

    CommandLine:
        python -m vtool_ibeis.other atleast_3channels

    Doctest:
        >>> from vtool_ibeis.image import *  # NOQA
        >>> import vtool_ibeis as vt
        >>> assert atleast_3channels(np.zeros((10, 10))).shape[-1] == 3
        >>> assert atleast_3channels(np.zeros((10, 10, 1))).shape[-1] == 3
        >>> assert atleast_3channels(np.zeros((10, 10, 3))).shape[-1] == 3
        >>> assert atleast_3channels(np.zeros((10, 10, 4))).shape[-1] == 4
    """
    # atleast_shape(arr, (None, None, 3))
    ndims = len(arr.shape)
    if ndims == 2:
        res = np.tile(arr[:, :, None], 3)
        return res
    elif ndims == 3:
        h, w, c = arr.shape
        if c == 1:
            res = np.tile(arr, 3)
        elif c in [3, 4]:
            res = arr.copy() if copy else arr
        else:
            raise ValueError('Cannot handle ndims={}'.format(ndims))
    else:
        raise ValueError('Cannot handle arr.shape={}'.format(arr.shape))
    return res


def iter_reduce_ufunc(ufunc, arr_iter, out=None):
    """
    constant memory iteration and reduction

    applys ufunc from left to right over the input arrays

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> arr_list = [
        ...     np.array([0, 1, 2, 3, 8, 9]),
        ...     np.array([4, 1, 2, 3, 4, 5]),
        ...     np.array([0, 5, 2, 3, 4, 5]),
        ...     np.array([1, 1, 6, 3, 4, 5]),
        ...     np.array([0, 1, 2, 7, 4, 5])
        ... ]
        >>> memory = np.array([9, 9, 9, 9, 9, 9])
        >>> gen_memory = memory.copy()
        >>> def arr_gen(arr_list, gen_memory):
        ...     for arr in arr_list:
        ...         gen_memory[:] = arr
        ...         yield gen_memory
        >>> print('memory = %r' % (memory,))
        >>> print('gen_memory = %r' % (gen_memory,))
        >>> ufunc = np.maximum
        >>> res1 = iter_reduce_ufunc(ufunc, iter(arr_list), out=None)
        >>> res2 = iter_reduce_ufunc(ufunc, iter(arr_list), out=memory)
        >>> res3 = iter_reduce_ufunc(ufunc, arr_gen(arr_list, gen_memory), out=memory)
        >>> print('res1       = %r' % (res1,))
        >>> print('res2       = %r' % (res2,))
        >>> print('res3       = %r' % (res3,))
        >>> print('memory     = %r' % (memory,))
        >>> print('gen_memory = %r' % (gen_memory,))
        >>> assert np.all(res1 == res2)
        >>> assert np.all(res2 == res3)
    """
    # Get first item in iterator
    try:
        initial = next(arr_iter)
    except StopIteration:
        return None
    # Populate the outvariable if specified otherwise make a copy of the first
    # item to be the output memory
    if out is not None:
        out[:] = initial
    else:
        out = initial.copy()
    # Iterate and reduce
    for arr in arr_iter:
        ufunc(out, arr, out=out)
    return out


def clipnorm(arr, min_, max_, out=None):
    """
    normalizes arr to the range 0 to 1 using min_ and max_ as clipping bounds
    """
    if max_ == 1 and min_ == 0:
        if out is not None:
            out[:] = arr
        else:
            out = arr.copy()
        return out
    out_args = tuple() if out is None else (out,)
    arr_ = np.subtract(arr, min_, *out_args)
    arr_ = np.divide(arr_, max_ - min_, *out_args)
    arr_ = np.clip(arr_, 0.0, 1.0, *out_args)
    return arr_


def intersect1d_reduce(arr_list, assume_unique=False):
    arr_iter = iter(arr_list)
    out = next(arr_iter)
    for arr in arr_iter:
        out = np.intersect1d(out, arr, assume_unique=assume_unique)
    return out


def componentwise_dot(arr1, arr2):
    """
    a dot product is a componentwise multiplication of
    two vector and then a sum.

    Args:
        arr1 (ndarray)
        arr2 (ndarray):

    Returns:
        ndarray: cosangle

    Example:
        >>> # DISABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> np.random.seed(0)
        >>> arr1 = np.random.rand(3, 128)
        >>> arr1 = arr1 / np.linalg.norm(arr1, axis=1)[:, None]
        >>> arr2 = arr1
        >>> cosangle = componentwise_dot(arr1, arr2)
        >>> result = str(cosangle)
        >>> print(result)
        [ 1.  1.  1.]
    """
    cosangle = np.multiply(arr1, arr2).sum(axis=-1).T
    return cosangle


def intersect2d_indices(A, B):
    r"""
    Args:
        A (ndarray[ndims=2]):
        B (ndarray[ndims=2]):

    Returns:
        tuple: (ax_list, bx_list)

    CommandLine:
        python -m vtool_ibeis.other --test-intersect2d_indices

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> # build test data
        >>> A = np.array([[ 158,  171], [ 542,  297], [ 955, 1113], [ 255, 1254], [ 976, 1255], [ 170, 1265]])
        >>> B = np.array([[ 117,  211], [ 158,  171], [ 255, 1254], [ 309,  328], [ 447, 1148], [ 750,  357], [ 976, 1255]])
        >>> # execute function
        >>> (ax_list, bx_list) = intersect2d_indices(A, B)
        >>> # verify results
        >>> result = str((ax_list, bx_list))
        >>> print(result)
    """
    flag_list1, flag_list2 = intersect2d_flags(A, B)
    ax_list = np.flatnonzero(flag_list1)
    bx_list = np.flatnonzero(flag_list2)
    return ax_list, bx_list


def intersect2d_flags(A, B):
    r"""
    Checks intersection of rows of A against rows of B

    Args:
        A (ndarray[ndims=2]):
        B (ndarray[ndims=2]):

    Returns:
        tuple: (flag_list1, flag_list2)

    CommandLine:
        python -m vtool_ibeis.other --test-intersect2d_flags

    SeeAlso:
        np.in1d - the one dimensional version

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> A = np.array([[609, 307], [ 95, 344], [  1, 690]])
        >>> B = np.array([[ 422, 1148], [ 422,  968], [ 481, 1148], [ 750, 1132], [ 759,  159]])
        >>> (flag_list1, flag_list2) = intersect2d_flags(A, B)
        >>> result = str((flag_list1, flag_list2))
        >>> print(result)
    """
    A_, B_, C_  = intersect2d_structured_numpy(A, B)
    flag_list1 = flag_intersection(A_, C_)
    flag_list2 = flag_intersection(B_, C_)
    return flag_list1, flag_list2


def flag_intersection(arr1, arr2):
    r"""
    Flags the rows in `arr1` that contain items in `arr2`

    Returns:
        ndarray: flags where len(flags) == len(arr1)

    Example0:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> arr1 = np.array([0, 1, 2, 3, 4, 5])
        >>> arr2 = np.array([2, 6, 4])
        >>> flags = flag_intersection(arr1, arr2)
        >>> assert len(flags) == len(arr1)
        >>> result = ('flags = %s' % (ub.repr2(flags),))
        >>> print(result)

    Example1:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> import vtool_ibeis as vt
        >>> arr1 = np.array([[0, 0], [0, 1], [0, 2], [0, 3], [0, 4], [0, 5]])
        >>> arr2 = np.array([[0, 2], [0, 6], [0, 4], [3, 0]])
        >>> arr1, arr2 = vt.structure_rows(arr1, arr2)
        >>> flags = flag_intersection(arr1, arr2)
        >>> assert len(flags) == len(arr1)
        >>> result = ('flags = %s' % (ub.repr2(flags),))
        >>> print(result)

    Example2:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> arr1 = np.array([0, 1, 2, 3, 4, 5])
        >>> arr2 = np.array([])
        >>> flags = flag_intersection(arr1, arr2)
        >>> assert len(flags) == len(arr1)
        >>> flags = flag_intersection(np.array([]), np.array([2, 6, 4]))
        >>> assert len(flags) == 0

    Timeit:
        >>> setup = ut.codeblock(
        >>>     r'''
                import vtool_ibeis as vt
                import numpy as np
                rng = np.random.RandomState(0)
                arr1 = rng.randint(0, 100, 100000).reshape(-1, 2)
                arr2 = rng.randint(0, 100, 1000).reshape(-1, 2)
                arr1_, arr2_ = vt.structure_rows(arr1, arr2)
                ''')
        >>> stmt_list = ut.codeblock(
        >>>     '''
                np.array([row in arr2_ for row in arr1_])
                np.logical_or.reduce([arr1_ == row_ for row_ in arr2_]).ravel()
                vt.iter_reduce_ufunc(np.logical_or, (arr1_ == row_ for row_ in arr2_)).ravel()
                ''').split('\n')
        >>> out = ut.timeit_compare(stmt_list, setup=setup, iterations=3)
    """
    import vtool_ibeis as vt
    if arr1.size == 0 or arr2.size == 0:
        flags = np.full(arr1.shape[0], False, dtype=bool)
        #return np.empty((0,), dtype=bool)
    else:
        # flags = np.logical_or.reduce([arr1 == row for row in arr2]).T[0]
        flags = vt.iter_reduce_ufunc(np.logical_or, (arr1 == row_ for row_ in arr2)).ravel()
    return flags


def structure_rows(*arrs):
    r"""
    CommandLine:
        python -m vtool_ibeis.other structure_rows

    SeeAlso:
        unstructure_rows

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> arr1 = np.array([[609, 307], [ 95, 344], [  1, 690]])
        >>> arr2 = np.array([[ 422, 1148], [ 422,  968], [ 481, 1148], [ 750, 1132], [ 759,  159]])
        >>> arrs = (arr1, arr2)
        >>> structured_arrs = structure_rows(*arrs)
        >>> unstructured_arrs = unstructure_rows(*structured_arrs)
        >>> assert np.all(unstructured_arrs[0] == arrs[0])
        >>> assert np.all(unstructured_arrs[1] == arrs[1])
        >>> union_ = np.union1d(*structured_arrs)
        >>> union, = unstructure_rows(union_)
        >>> assert len(union.shape) == 2
    """
    arr0 = arrs[0]
    ncols = arr0.shape[1]
    dtype = {'names': ['f%d' % (i,) for i in range(ncols)],
             'formats': ncols * [arr0.dtype]}
    for arr in arrs:
        assert len(arr.shape) == 2, 'arrays must be 2d'
        assert arr.dtype == arr0.dtype, 'arrays must share the same dtype'
        assert arr.shape[1] == ncols, 'arrays must share column shape'
    structured_arrs = []
    for arr in arrs:
        arr_ = np.ascontiguousarray(arr).view(dtype)
        structured_arrs.append(arr_)
    return structured_arrs


def unstructure_rows(*structured_arrs):
    r"""
    SeeAlso:
        structure_rows
    """
    # TODO: assert arr.dtype.fields are all the same type
    unstructured_arrs = [arr.view(list(arr.dtype.fields.values())[0][0])
                         for arr in structured_arrs]
    unstructured_arrs = []
    for arr_ in structured_arrs:
        dtype = list(arr_.dtype.fields.values())[0][0]
        arr = arr_.view(dtype).reshape(-1, 2)
        unstructured_arrs.append(arr)
    return unstructured_arrs


def intersect2d_structured_numpy(arr1, arr2, assume_unique=False):
    """
    Args:
        arr1: unstructured 2d array
        arr2: unstructured 2d array

    Returns:
        A_, B_, C_ - structured versions of arr1, and arr2, and their structured intersection

    References:
        http://stackoverflow.com/questions/16970982/find-unique-rows-in-numpy-array
        http://stackoverflow.com/questions/8317022/get-intersecting-rows-across-two-2d-numpy-arrays
    """
    ncols = arr1.shape[1]
    assert arr1.dtype == arr2.dtype, (
        'arr1 and arr2 must have the same dtypes.'
        'arr1.dtype=%r, arr2.dtype=%r' % (arr1.dtype, arr2.dtype))
    # [('f%d' % i, arr1.dtype) for i in range(ncols)]
    #dtype = np.dtype([('f%d' % i, arr1.dtype) for i in range(ncols)])
    #dtype = {'names': ['f{}'.format(i) for i in range(ncols)],
    #         'formats': ncols * [arr1.dtype]}
    dtype = {'names': ['f%d' % (i,) for i in range(ncols)],
             'formats': ncols * [arr1.dtype]}
    #try:
    A_ = np.ascontiguousarray(arr1).view(dtype)
    B_ = np.ascontiguousarray(arr2).view(dtype)
    C_ = np.intersect1d(A_, B_, assume_unique=assume_unique)
    #C = np.intersect1d(arr1.view(dtype),
    #                   arr2.view(dtype),
    #                   assume_unique=assume_unique)
    #except ValueError:
    #    C = np.intersect1d(A.copy().view(dtype),
    #                       B.copy().view(dtype),
    #                       assume_unique=assume_unique)
    return A_, B_, C_


def intersect2d_numpy(A, B, assume_unique=False, return_indices=False):
    """
    References::
        http://stackoverflow.com/questions/8317022/get-intersecting-rows-across-two-2d-numpy-arrays/8317155#8317155

    Args:
        A (ndarray[ndims=2]):
        B (ndarray[ndims=2]):
        assume_unique (bool):

    Returns:
        ndarray[ndims=2]: C

    CommandLine:
        python -m vtool_ibeis.other --test-intersect2d_numpy

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> # build test data
        >>> A = np.array([[  0,  78,  85, 283, 396, 400, 403, 412, 535, 552],
        ...               [152,  98,  32, 260, 387, 285,  22, 103,  55, 261]]).T
        >>> B = np.array([[403,  85, 412,  85, 815, 463, 613, 552],
        ...                [ 22,  32, 103, 116, 188, 199, 217, 254]]).T
        >>> assume_unique = False
        >>> # execute function
        >>> C, Ax, Bx = intersect2d_numpy(A, B, return_indices=True)
        >>> # verify results
        >>> result = str((C.T, Ax, Bx))
        >>> print(result)
        (array([[ 85, 403, 412],
               [ 32,  22, 103]]), array([2, 6, 7]), array([0, 1, 2]))

    Example2:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> A = np.array([[1, 2, 3], [1, 1, 1]])
        >>> B = np.array([[1, 2, 3], [1, 2, 14]])
        >>> C, Ax, Bx = intersect2d_numpy(A, B, return_indices=True)
        >>> result = str((C, Ax, Bx))
        >>> print(result)
        (array([[1, 2, 3]]), array([0]), array([0]))
    """
    nrows, ncols = A.shape
    A_, B_, C_ = intersect2d_structured_numpy(A, B, assume_unique)
    # This last bit is optional if you're okay with "C" being a structured array...
    C = C_.view(A.dtype).reshape(-1, ncols)
    if return_indices:
        ax_list = np.flatnonzero(flag_intersection(A_, C_))
        bx_list = np.flatnonzero(flag_intersection(B_, C_))
        return C, ax_list, bx_list
    else:
        return C


def nearest_point(x, y, pts, mode='random'):
    """ finds the nearest point(s) in pts to (x, y) """
    dists = (pts.T[0] - x) ** 2 + (pts.T[1] - y) ** 2
    fx = dists.argmin()
    mindist = dists[fx]
    other_fx = np.where(mindist == dists)[0]
    if len(other_fx) > 0:
        if mode == 'random':
            np.random.shuffle(other_fx)
            fx = other_fx[0]
        if mode == 'all':
            fx = other_fx
        if mode == 'first':
            fx = fx
    return fx, mindist


def get_uncovered_mask(covered_array, covering_array):
    r"""
    Args:
        covered_array (ndarray):
        covering_array (ndarray):

    Returns:
        ndarray: flags

    CommandLine:
        python -m vtool_ibeis.other --test-get_uncovered_mask

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> covered_array = [1, 2, 3, 4, 5]
        >>> covering_array = [2, 4, 5]
        >>> flags = get_uncovered_mask(covered_array, covering_array)
        >>> result = str(flags)
        >>> print(result)
        [ True False  True False False]

    Example2:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> covered_array = [1, 2, 3, 4, 5]
        >>> covering_array = []
        >>> flags = get_uncovered_mask(covered_array, covering_array)
        >>> result = str(flags)
        >>> print(result)
        [ True  True  True  True  True]

    Example3:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> covered_array = np.array([
        ...  [1, 2, 3],
        ...  [4, 5, 6],
        ...  [7, 8, 9],
        ... ], dtype=np.int32)
        >>> covering_array = [2, 4, 5]
        >>> flags = get_uncovered_mask(covered_array, covering_array)
        >>> result = ub.repr2(flags, with_dtype=True)
        >>> print(result)

        np.array([[ True, False,  True],
                  [False, False,  True],
                  [ True,  True,  True]], dtype=bool)

    Ignore::
        covering_array = [1, 2, 3, 4, 5, 6, 7]
        %timeit get_uncovered_mask(covered_array, covering_array)
        100000 loops, best of 3: 18.6 µs per loop
        %timeit get_uncovered_mask2(covered_array, covering_array)
        100000 loops, best of 3: 16.9 µs per loop


    """
    import vtool_ibeis as vt
    if len(covering_array) == 0:
        return np.ones(np.shape(covered_array), dtype=bool)
    else:
        flags_iter = (np.not_equal(covered_array, item) for item in covering_array)
        mask_array = vt.iter_reduce_ufunc(np.logical_and, flags_iter)
        return mask_array
    #if len(covering_array) == 0:
    #    return np.ones(np.shape(covered_array), dtype=bool)
    #else:
    #    flags_list = (np.not_equal(covered_array, item) for item in covering_array)
    #    mask_array = and_lists(*flags_list)
    #    return mask_array


#def get_uncovered_mask2(covered_array, covering_array):
#    if len(covering_array) == 0:
#        return np.ones(np.shape(covered_array), dtype=bool)
#    else:
#        flags_iter = (np.not_equal(covered_array, item) for item in covering_array)
#        mask_array = vt.iter_reduce_ufunc(np.logical_and, flags_iter)
#        return mask_array


def get_covered_mask(covered_array, covering_array):
    return ~get_uncovered_mask(covered_array, covering_array)


def mult_lists(*args):
    return np.multiply.reduce(args)


def or_lists(*args):
    """
    Like np.logical_and, but can take more than 2 arguments

    SeeAlso:
        and_lists
    """
    flags = np.logical_or.reduce(args)
    return flags


def and_lists(*args):
    """
    Like np.logical_and, but can take more than 2 arguments

    CommandLine:
        python -m vtool_ibeis.other --test-and_lists

    SeeAlso:
       or_lists

    Example1:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> arg1 = np.array([1, 1, 1, 1,])
        >>> arg2 = np.array([1, 1, 0, 1,])
        >>> arg3 = np.array([0, 1, 0, 1,])
        >>> args = (arg1, arg2, arg3)
        >>> flags = and_lists(*args)
        >>> result = str(flags)
        >>> print(result)
        [False  True False  True]

    Example2:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> size = 10000
        >>> rng = np.random.RandomState(0)
        >>> arg1 = rng.randint(2, size=size)
        >>> arg2 = rng.randint(2, size=size)
        >>> arg3 = rng.randint(2, size=size)
        >>> args = (arg1, arg2, arg3)
        >>> flags = and_lists(*args)
        >>> # ensure equal division
        >>> segments = 5
        >>> validx = np.where(flags)[0]
        >>> endx = int(segments * (validx.size // (segments)))
        >>> parts = np.split(validx[:endx], segments)
        >>> result = str(list(map(np.sum, parts)))
        >>> print(result)
        [243734, 714397, 1204989, 1729375, 2235191]

    %timeit reduce(np.logical_and, args)
    %timeit np.logical_and.reduce(args)  # wins with more data
    """
    return np.logical_and.reduce(args)


def rowwise_operation(arr1, arr2, op):
    """
    DEPRICATE THIS IS POSSIBLE WITH STRICTLY BROADCASTING AND
    USING np.newaxis

    DEPRICATE, numpy has better ways of doing this.
    Is the rowwise name correct? Should it be colwise?

    performs an operation between an
    (N x A x B ... x Z) array with an
    (N x 1) array
    """
    # FIXME: not sure this is the correct terminology
    assert arr1.shape[0] == arr2.shape[0]
    broadcast_dimensions = arr1.shape[1:]  # need padding for
    tileshape = tuple(list(broadcast_dimensions) + [1])
    arr2_ = np.rollaxis(np.tile(arr2, tileshape), -1)
    rowwise_result = op(arr1, arr2_)
    return rowwise_result


def colwise_operation(arr1, arr2, op):
    arr1T = arr1.T
    arr2T = arr2.T
    rowwise_result = rowwise_operation(arr1T, arr2T, op)
    colwise_result = rowwise_result.T
    return colwise_result


def compare_matrix_columns(matrix, columns, comp_op=np.equal, logic_op=np.logical_or):
    """
    REPLACE WITH:
        qfx2_invalid = logic_op.reduce([comp_op([:, None], qfx2_normnid) for col1 in qfx2_topnid.T])

    """
    # FIXME: Generalize
    #row_matrix = matrix.T
    #row_list   = columns.T
    return compare_matrix_to_rows(matrix.T, columns.T, comp_op=comp_op, logic_op=logic_op).T


def compare_matrix_to_rows(row_matrix, row_list, comp_op=np.equal, logic_op=np.logical_or):
    """
    Compares each row in row_list to each row in row matrix using comp_op
    Both must have the same number of columns.
    Performs logic_op on the results of each individual row

    SeeAlso:
        ibeis.algo.hots.nn_weights.mark_name_valid_normalizers

    compop   = np.equal
    logic_op = np.logical_or
    """
    row_result_list = [np.array([comp_op(matrow, row) for matrow in row_matrix])
                       for row in row_list]
    output = row_result_list[0]
    for row_result in row_result_list[1:]:
        logic_op(output, row_result, out=output)
        #output = logic_op(output, row_result)
    return output


def norm01(array, dim=None):
    """
    normalizes a numpy array from 0 to 1 based in its extent

    Args:
        array (ndarray):
        dim   (int):

    Returns:
        ndarray:

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> array = np.array([ 22, 1, 3, 2, 10, 42, ])
        >>> dim = None
        >>> array_norm = norm01(array, dim)
        >>> result = ub.repr2(array_norm, precision=3)
        >>> print(result)
    """
    if not ut.is_float(array):
        array = array.astype(np.float32)
    array_max  = array.max(dim)
    array_min  = array.min(dim)
    array_exnt = np.subtract(array_max, array_min)
    array_norm = np.divide(np.subtract(array, array_min), array_exnt)
    return array_norm


def weighted_geometic_mean_unnormalized(data, weights):
    import vtool_ibeis as vt
    terms = [x ** w for x, w in zip(data, weights)]
    termprod = vt.iter_reduce_ufunc(np.multiply, iter(terms))
    return termprod


def weighted_geometic_mean(data, weights):
    r"""
    Args:
        data (list of ndarrays):
        weights (ndarray):

    Returns:
        ndarray: gmean_

    CommandLine:
        python -m vtool_ibeis.other --test-weighted_geometic_mean

    References:
        https://en.wikipedia.org/wiki/Weighted_geometric_mean

    SeeAlso:
        scipy.stats.mstats.gmean

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> data = [.9, .5]
        >>> weights = np.array([1.0, .5])
        >>> gmean_ = weighted_geometic_mean(data, weights)
        >>> result = ('gmean_ = %.3f' % (gmean_,))
        >>> print(result)
        gmean_ = 0.740

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> rng = np.random.RandomState(0)
        >>> img1 = rng.rand(4, 4)
        >>> img2 = rng.rand(4, 4)
        >>> data = [img1, img2]
        >>> weights = np.array([.5, .5])
        >>> gmean_ = weighted_geometic_mean(data, weights)
        >>> result = ub.hzcat(['gmean_ = ', ub.repr2(gmean_, precision=2, with_dtype=True)])
        >>> print(result)

    Ignore:
        res1 = ((img1 ** .5 * img2 ** .5)) ** 1
        res2 = np.sqrt(img1 * img2)
    """
    import vtool_ibeis as vt
    terms = [np.asarray(x ** w) for x, w in zip(data, weights)]
    termprod = vt.iter_reduce_ufunc(np.multiply, iter(terms))
    exponent = 1 / np.sum(weights)
    gmean_ = termprod ** exponent
    return gmean_


def grab_webcam_image():
    """
    References:
        http://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_gui/py_video_display/py_video_display.html

    CommandLine:
        python -m vtool_ibeis.other --test-grab_webcam_image --show

    Example:
        >>> # SCRIPT
        >>> from vtool_ibeis.other import *  # NOQA
        >>> import vtool_ibeis as vt
        >>> img = grab_webcam_image()
        >>> # xdoctest: +REQUIRES(--show)
        >>> import plottool_ibeis as pt
        >>> pt.imshow(img)
        >>> vt.imwrite('webcap.jpg', img)
        >>> ut.show_if_requested()
    """
    import cv2
    cap = cv2.VideoCapture(0)
    # Capture frame-by-frame
    ret, img = cap.read()
    # When everything done, release the capture
    cap.release()
    return img


#def xor_swap(arr1, arr2, inplace=True):
#    if not inplace:
#        arr1 = arr1.copy()
#        arr2 = arr2.copy()
#    np.bitwise_xor(arr1, arr2, out=arr1)
#    np.bitwise_xor(arr1, arr2, out=arr2)
#    np.bitwise_xor(arr1, arr2, out=arr1)
#    return arr1, arr2


def find_first_true_indices(flags_list):
    """
    TODO: move to vtool_ibeis

    returns a list of indexes where the index is the first True position
    in the corresponding sublist or None if it does not exist

    in other words: for each row finds the smallest True column number or None

    Args:
        flags_list (list): list of lists of booleans

    CommandLine:
        python -m utool.util_list --test-find_first_true_indices

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> # build test data
        >>> flags_list = [[True, False, True],
        ...               [False, False, False],
        ...               [False, True, True],
        ...               [False, False, True]]
        >>> # execute function
        >>> index_list = find_first_true_indices(flags_list)
        >>> # verify results
        >>> result = str(index_list)
        >>> print(result)
        [0, None, 1, 2]
    """
    def tryget_fisrt_true(flags):
        index_list = np.where(flags)[0]
        index = None if len(index_list) == 0 else index_list[0]
        return index
    index_list = [tryget_fisrt_true(flags) for flags in flags_list]
    return index_list


def find_k_true_indicies(flags_list, k):
    r"""
    Uses output of either this function or find_first_true_indices
    to find the next index of true flags

    Args:
        flags_list (list): list of lists of booleans

    CommandLine:
        python -m utool.util_list --test-find_next_true_indices

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> flags_list = [[False, False, True],
        ...               [False, False, False],
        ...               [False, True, True],
        ...               [True, True, True]]
        >>> k = 2
        >>> indices = find_k_true_indicies(flags_list, k)
        >>> result = str(indices)
        >>> print(result)
        [array([2]), None, array([1, 2]), array([0, 1])]
    """

    if False:
        import vtool_ibeis as vt
        flags_list = np.array(flags_list)
        rowxs, colxs = np.where(flags_list)
        first_k_groupxs = [groupx[0:k] for groupx in vt.group_indices(rowxs)[1]]
        chosen_xs = np.hstack(first_k_groupxs)
        flat_xs = np.ravel_multi_index((rowxs.take(chosen_xs), colxs.take(chosen_xs)), flags_list.shape)
        flat_xs
    def tryget_k_true(flags):
        index_list = np.where(flags)[0]
        index = None if len(index_list) == 0 else index_list[0:k]
        return index
    index_list = [tryget_k_true(flags) for flags in flags_list]
    return index_list


def find_next_true_indices(flags_list, offset_list):
    r"""
    Uses output of either this function or find_first_true_indices
    to find the next index of true flags

    Args:
        flags_list (list): list of lists of booleans

    CommandLine:
        python -m utool.util_list --test-find_next_true_indices

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> # build test data
        >>> flags_list = [[True, False, True],
        ...               [False, False, False],
        ...               [False, True, True],
        ...               [False, False, True]]
        >>> offset_list = find_first_true_indices(flags_list)
        >>> # execute function
        >>> index_list = find_next_true_indices(flags_list, offset_list)
        >>> # verify results
        >>> result = str(index_list)
        >>> print(result)
        [2, None, 2, None]
    """
    def tryget_next_true(flags, offset_):
        offset = offset_ + 1
        relative_flags = flags[offset:]
        rel_index_list = np.where(relative_flags)[0]
        index = None if len(rel_index_list) == 0 else rel_index_list[0] + offset
        return index
    index_list = [None if offset is None else tryget_next_true(flags, offset)
                  for flags, offset in zip(flags_list, offset_list)]
    return index_list


def ensure_rng(seed=None):
    """
    Returns a numpy random number generator given a seed.
    """
    if seed is None:
        rng = np.random
    elif isinstance(seed, np.random.RandomState):
        rng = seed
    else:
        rng = np.random.RandomState(seed)
    return rng


def safe_extreme(arr, op, fill=np.nan, finite=False, nans=True):
    """
    Applies an exterme operation to an 1d array (typically max/min) but ensures
    a value is always returned even in operations without identities. The
    default identity must be specified using the `fill` argument.

    Args:
        arr (ndarray): 1d array to take extreme of
        op (func): vectorized operation like np.max to apply to array
        fill (float): return type if arr has no elements (default = nan)
        finite (bool): if True ignores non-finite values (default = False)
        nans (bool): if False ignores nans (default = True)
    """
    if arr is None:
        extreme = fill
    else:
        arr = np.asarray(arr)
        if finite:
            arr = arr.compress(np.isfinite(arr))
        if not nans:
            arr = arr.compress(np.logical_not(np.isnan(arr)))
        if len(arr) == 0:
            extreme =  fill
        else:
            extreme = op(arr)
    return extreme


def safe_argmax(arr, fill=np.nan, finite=False, nans=True):
    """
    Doctest:
        >>> from vtool_ibeis.other import *
        >>> assert safe_argmax([np.nan, np.nan], nans=False) == 0
        >>> assert safe_argmax([-100, np.nan], nans=False) == 0
        >>> assert safe_argmax([np.nan, -100], nans=False) == 1
        >>> assert safe_argmax([-100, 0], nans=False) == 1
        >>> assert np.isnan(safe_argmax([]))
    """
    if len(arr) == 0:
        return fill
    extreme = safe_max(arr, fill=fill, finite=finite, nans=nans)
    if np.isnan(extreme):
        arg_extreme = np.where(np.isnan(arr))[0][0]
    else:
        arg_extreme = np.where(arr == extreme)[0][0]
    return arg_extreme


def safe_max(arr, fill=np.nan, finite=False, nans=True):
    r"""
    Args:
        arr (ndarray): 1d array to take max of
        fill (float): return type if arr has no elements (default = nan)
        finite (bool): if True ignores non-finite values (default = False)
        nans (bool): if False ignores nans (default = True)

    CommandLine:
        python -m vtool_ibeis.other safe_max --show

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> arrs = [[], [np.nan], [-np.inf, np.nan, np.inf], [np.inf], [np.inf, 1], [0, 1]]
        >>> arrs = [np.array(arr) for arr in arrs]
        >>> fill = np.nan
        >>> results1 = [safe_max(arr, fill, finite=False, nans=True) for arr in arrs]
        >>> results2 = [safe_max(arr, fill, finite=True, nans=True) for arr in arrs]
        >>> results3 = [safe_max(arr, fill, finite=True, nans=False) for arr in arrs]
        >>> results4 = [safe_max(arr, fill, finite=False, nans=False) for arr in arrs]
        >>> results = [results1, results2, results3, results4]
        >>> result = ('results = %s' % (ub.repr2(results, nl=1),))
        >>> print(result)

        results = [
            [nan, nan, nan, inf, inf, 1],
            [nan, nan, nan, nan, 1.0, 1],
            [nan, nan, nan, nan, 1.0, 1],
            [nan, nan, inf, inf, inf, 1],
        ]
    """
    return safe_extreme(arr, np.max, fill, finite, nans)


def safe_min(arr, fill=np.nan, finite=False, nans=True):
    """
    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> arrs = [[], [np.nan], [-np.inf, np.nan, np.inf], [np.inf], [np.inf, 1], [0, 1]]
        >>> arrs = [np.array(arr) for arr in arrs]
        >>> fill = np.nan
        >>> results1 = [safe_min(arr, fill, finite=False, nans=True) for arr in arrs]
        >>> results2 = [safe_min(arr, fill, finite=True, nans=True) for arr in arrs]
        >>> results3 = [safe_min(arr, fill, finite=True, nans=False) for arr in arrs]
        >>> results4 = [safe_min(arr, fill, finite=False, nans=False) for arr in arrs]
        >>> results = [results1, results2, results3, results4]
        >>> result = ('results = %s' % (ub.repr2(results, nl=1),))
        >>> print(result)

        results = [
            [nan, nan, nan, inf, 1.0, 0],
            [nan, nan, nan, nan, 1.0, 0],
            [nan, nan, nan, nan, 1.0, 0],
            [nan, nan, -inf, inf, 1.0, 0],
        ]
    """
    return safe_extreme(arr, np.min, fill, finite, nans)


def safe_div(a, b):
    return None if a is None or b is None else a / b


def multigroup_lookup_naive(lazydict, keys_list, subkeys_list, custom_func):
    r"""
    Slow version of multigroup_lookup. Makes a call to custom_func for each
    item in zip(keys_list, subkeys_list).

    SeeAlso:
        vt.multigroup_lookup
    """
    data_lists = []
    for keys, subkeys in zip(keys_list, subkeys_list):
        subvals_list = [
            custom_func(lazydict, key, [subkey])[0]
            for key, subkey in zip(keys, subkeys)
        ]
        data_lists.append(subvals_list)
    return data_lists


def multigroup_lookup(lazydict, keys_list, subkeys_list, custom_func):
    r"""
    Efficiently calls custom_func for each item in zip(keys_list, subkeys_list)
    by grouping subkeys to minimize the number of calls to custom_func.

    We are given multiple lists of keys, and subvals.
    The goal is to group the subvals by keys and apply the subval lookups
    (a call to a function) to the key only once and at the same time.

    Args:
        lazydict (dict of utool.LazyDict):
        keys_list (list):
        subkeys_list (list):
        custom_func (func): must have signature custom_func(lazydict, key, subkeys)

    SeeAlso:
        vt.multigroup_lookup_naive - unoptomized version, but simple to read

    Example:
        >>> # SLOW_DOCTEST
        >>> # xdoctest: +SKIP
        >>> from vtool_ibeis.other import *  # NOQA
        >>> import vtool_ibeis as vt
        >>> fpath_list = [ut.grab_test_imgpath(key) for key in ut.util_grabdata.get_valid_test_imgkeys()]
        >>> lazydict = {count: vt.testdata_annot_metadata(fpath) for count, fpath in enumerate(fpath_list)}
        >>> aids_list = np.array([(3, 2), (0, 2), (1, 2), (2, 3)])
        >>> fms       = np.array([[2, 5], [2, 3], [2, 1], [3, 4]])
        >>> keys_list = aids_list.T
        >>> subkeys_list = fms.T
        >>> def custom_func(lazydict, key, subkeys):
        >>>     annot = lazydict[key]
        >>>     kpts = annot['kpts']
        >>>     rchip = annot['rchip']
        >>>     kpts_m = kpts.take(subkeys, axis=0)
        >>>     warped_patches = vt.get_warped_patches(rchip, kpts_m)[0]
        >>>     return warped_patches
        >>> data_lists1 = multigroup_lookup(lazydict, keys_list, subkeys_list, custom_func)
        >>> data_lists2 = multigroup_lookup_naive(lazydict, keys_list, subkeys_list, custom_func)
        >>> vt.sver_c_wrapper.asserteq(data_lists1, data_lists2)

    Example:
        >>> keys_list = [np.array([]), np.array([]), np.array([])]
        >>> subkeys_list = [np.array([]), np.array([]), np.array([])]
    """
    import vtool_ibeis as vt
    # Group the keys in each multi-list individually
    multi_groups = [vt.group_indices(keys) for keys in keys_list]
    # Combine keys across multi-lists usings a dict_stack
    dict_list = [dict(zip(k, v)) for k, v in multi_groups]
    nested_order = ut.dict_stack2(dict_list, default=[])
    # Use keys and values for explicit ordering
    group_key_list = list(nested_order.keys())
    if len(group_key_list) == 0:
        return multigroup_lookup_naive(lazydict, keys_list, subkeys_list, custom_func)
    group_subxs_list = list(nested_order.values())
    # Extract unique and flat subkeys.
    # Maintain an information to invert back into multi-list form
    group_uf_subkeys_list = []
    group_invx_list = []
    group_cumsum_list = []
    for key, subxs in zip(group_key_list, group_subxs_list):
        # Group subkeys for each key
        subkey_group = vt.ziptake(subkeys_list, subxs, axis=0)
        flat_subkeys, group_cumsum = ut.invertible_flatten2(subkey_group)
        unique_subkeys, invx = np.unique(flat_subkeys, return_inverse=True)
        # Append info
        group_uf_subkeys_list.append(unique_subkeys)
        group_invx_list.append(invx)
        group_cumsum_list.append(group_cumsum)
    # Apply custom function (lookup) to unique each key and its flat subkeys
    group_subvals_list = [
        custom_func(lazydict, key, subkeys)
        for key, subkeys in zip(group_key_list, group_uf_subkeys_list)
    ]
    # Efficiently invert values back into input shape
    # First invert the subkey groupings
    multi_subvals_list = [[] for _ in range(len(multi_groups))]
    _iter = zip(group_key_list, group_subvals_list, group_cumsum_list, group_invx_list)
    for key, subvals, group_cumsum, invx in _iter:
        nonunique_subvals = list(ub.take(subvals, invx))
        unflat_subvals_list = ut.unflatten2(nonunique_subvals, group_cumsum)
        for subvals_list, unflat_subvals in zip(multi_subvals_list, unflat_subvals_list):
            subvals_list.append(unflat_subvals)
    # Then invert the key groupings
    data_lists = []
    multi_groupxs_list = list(zip(*group_subxs_list))
    for subvals_list, groupxs in zip(multi_subvals_list, multi_groupxs_list):
        datas = vt.invert_apply_grouping(subvals_list, groupxs)
        data_lists.append(datas)
    return data_lists


def asserteq(output1, output2, thresh=1E-8, nestpath=None, level=0, lbl1=None,
             lbl2=None, output_lbl=None, verbose=True, iswarning=False):
    """
    recursive equality checks

    asserts that output1 and output2 are close to equal.
    """
    failed = False
    if lbl1 is None:
        lbl1 = ut.get_varname_from_stack(output1, N=1)
    if lbl2 is None:
        lbl2 = ut.get_varname_from_stack(output2, N=1)
    # Setup
    if nestpath is None:
        # record the path through the nested structure as testing goes on
        nestpath = []
    # print out these variables in all error cases
    common_keys = ['lbl1', 'lbl2', 'level', 'nestpath']
    # CHECK: types
    try:
        assert type(output1) == type(output2), 'types are not equal'
    except AssertionError as ex:
        print(type(output1))
        print(type(output2))
        ut.printex(ex, 'FAILED TYPE CHECKS',
                   keys=common_keys + [(type, 'output1'), (type, 'output2')],
                   iswarning=iswarning)
        failed = True
        if not iswarning:
            raise
    # CHECK: length
    if hasattr(output1, '__len__'):
        try:
            assert len(output1) == len(output2), 'lens are not equal'
        except AssertionError as ex:
            keys = common_keys + [(len, 'output1'), (len, 'output2'), ]
            ut.printex(ex, 'FAILED LEN CHECKS. ', keys=keys)
            raise
    # CHECK: ndarrays
    if isinstance(output1, np.ndarray):
        ndarray_keys = ['output1.shape', 'output2.shape']
        # CHECK: ndarray shape
        try:
            assert output1.shape == output2.shape, 'ndarray shapes are unequal'
        except AssertionError as ex:
            keys = common_keys + ndarray_keys
            ut.printex(ex, 'FAILED NUMPY SHAPE CHECKS.', keys=keys,
                       iswarning=iswarning)
            failed = True
            if not iswarning:
                raise
        # CHECK: ndarray equality
        try:
            passed, error = ut.almost_eq(output1, output2, thresh,
                                         ret_error=True)
            assert np.all(passed), 'ndarrays are unequal.'
        except AssertionError as ex:
            # Statistics on value difference and value difference
            # above the thresholds
            diff_stats = ut.get_stats(error)  # NOQA
            error_stats = ut.get_stats(error[error >= thresh])  # NOQA
            keys = common_keys + ndarray_keys + [
                (len, 'output1'), (len, 'output2'), ('diff_stats'),
                ('error_stats'), ('thresh'),
            ]
            PRINT_VAL_SAMPLE = True
            if PRINT_VAL_SAMPLE:
                keys += ['output1', 'output2']
            ut.printex(ex, 'FAILED NUMPY CHECKS.', keys=keys,
                       iswarning=iswarning)
            failed = True
            if not iswarning:
                raise
    # CHECK: list/tuple items
    elif isinstance(output1, (tuple, list)):
        for count, (item1, item2) in enumerate(zip(output1, output2)):
            # recursive call
            try:
                asserteq(
                    item1, item2, lbl1=lbl2, lbl2=lbl1, thresh=thresh,
                    nestpath=nestpath + [count], level=level + 1)
            except AssertionError as ex:
                ut.printex(ex, 'recursive call failed',
                           keys=common_keys + ['item1', 'item2', 'count'],
                           iswarning=iswarning)
                failed = True
                if not iswarning:
                    raise
    # CHECK: scalars
    else:
        try:
            assert output1 == output2, 'output1 != output2'
        except AssertionError as ex:
            print('nestpath= %r' % (nestpath,))
            ut.printex(ex, 'FAILED SCALAR CHECK.',
                       keys=common_keys + ['output1', 'output2'],
                       iswarning=iswarning)
            failed = True
            if not iswarning:
                raise
    if verbose and level == 0:
        if not failed:
            print('PASSED %s == %s' % (lbl1, lbl2))
        else:
            print('WARNING %s != %s' % (lbl1, lbl2))


def compare_implementations(func1, func2, args, show_output=False, lbl1='', lbl2='', output_lbl=None):
    """
    tests two different implementations of the same function
    """
    print('+ --- BEGIN COMPARE IMPLEMENTATIONS ---')
    func1_name = ut.get_funcname(func1)
    func2_name = ut.get_funcname(func2)
    print('func1_name = %r' % (func1_name,))
    print('func2_name = %r' % (func2_name,))
    # test both versions
    with ub.Timer('time func1=' + func1_name) as t1:
        output1 = func1(*args)
    with ub.Timer('time func2=' + func2_name) as t2:
        output2 = func2(*args)
    if t2.ellapsed == 0:
        t2.ellapsed = 1e9
    print('speedup = %r' % (t1.ellapsed / t2.ellapsed))
    try:
        asserteq(output1, output2, lbl1=lbl1, lbl2=lbl2, output_lbl=output_lbl)
        print('implementations are in agreement :) ')
    except AssertionError as ex:
        # prints out a nested list corresponding to nested structure
        ut.printex(ex, 'IMPLEMENTATIONS DO NOT AGREE', keys=[
            ('func1_name'),
            ('func2_name'), ]
        )
        raise
    finally:
        depth_profile1 = ut.depth_profile(output1)
        depth_profile2 = ut.depth_profile(output2)
        type_profile1 = ut.list_type_profile(output1)
        type_profile2 = ut.list_type_profile(output2)
        print('depth_profile1 = ' + ub.repr2(depth_profile1))
        print('depth_profile2 = ' + ub.repr2(depth_profile2))
        print('type_profile1 = ' + (type_profile1))
        print('type_profile2 = ' + (type_profile2))
    print('L ___ END COMPARE IMPLEMENTATIONS ___')
    return output1


def greedy_setcover(universe, subsets, weights=None):
    """
    Copied implmentation of greedy set cover from stack overflow. Needs work.

    References:
        http://stackoverflow.com/questions/7942312/of-greedy-set-cover-faster

    Example:
        >>> # SLOW_DOCTEST
        >>> # xdoctest: +SKIP
        >>> from vtool_ibeis.other import *  # NOQA
        >>> import vtool_ibeis as vt
        >>> universe = set([1,2,3,4])
        >>> subsets = [set([1,2]), set([1]), set([1,2,3]), set([1]), set([3,4]),
        >>>           set([4]), set([1,2]), set([3,4]), set([1,2,3,4])]
        >>> weights = [1, 1, 2, 2, 2, 3, 3, 4, 4]
        >>> chosen, costs = greedy_setcover(universe, subsets, weights)
        >>> print('Cover: %r' % (chosen,))
        >>> print('Total Cost: %r=sum(%r)' % (sum(costs), costs))
    """
    #unchosen = subsets.copy()
    uncovered = universe
    chosen = []
    costs = []

    def findMin(subsets, uncovered, weights):
        minCost = np.inf
        minElement = -1
        for i, s in enumerate(subsets):
            num_isect = len(s.intersection(uncovered))
            try:
                cost = weights[i] / num_isect
                if cost < minCost:
                    minCost = cost
                    minElement = i
            except ZeroDivisionError:
                pass
        return subsets[minElement], weights[minElement]

    while len(uncovered) != 0:
        S_i, cost = findMin(subsets, uncovered, weights)
        chosen.append(S_i)
        uncovered = uncovered.difference(S_i)
        costs.append(cost)
    return chosen, costs


def find_elbow_point(curve):
    """
    Finds the on the curve point furthest from the line defined by the
    endpoints of the curve.

    Args:
        curve (ndarray): a monotonic curve

    Returns:
        int: tradeoff_idx - this is an elbow point in the curve

    References:
        http://stackoverflow.com/questions/2018178/trade-off-point-on-curve

    CommandLine:
        python -m vtool_ibeis.other find_elbow_point --show

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> curve = np.exp(np.linspace(0, 10, 100))
        >>> tradeoff_idx = find_elbow_point(curve)
        >>> result = ('tradeoff_idx = %s' % (ub.repr2(tradeoff_idx),))
        >>> print(result)
        >>> assert tradeoff_idx == 76
        >>> # xdoctest: +REQUIRES(--show)
        >>> import plottool_ibeis as pt
        >>> import vtool_ibeis as vt
        >>> point = [tradeoff_idx, curve[tradeoff_idx]]
        >>> segment = np.array([[0, len(curve) - 1], [curve[0], curve[-1]]])
        >>> e1, e2 = segment.T
        >>> dist_point = vt.closest_point_on_line_segment(point, e1, e2)
        >>> dist_line = np.array([dist_point, point]).T
        >>> pt.plot(curve, 'r', label='curve')
        >>> pt.plot(point[0], point[1], 'go', markersize=10, label='tradeoff point')
        >>> pt.plot(dist_line[0], dist_line[1], '-xb')
        >>> pt.plot(segment[0], segment[1], '-xb')
        >>> pt.legend()
        >>> ut.show_if_requested()
    """
    num_points = len(curve)
    all_coords = np.vstack((np.arange(num_points), curve)).T
    np.array([np.arange(num_points), curve])
    first_point = all_coords[0]
    line_vec = all_coords[-1] - all_coords[0]
    line_vec_norm = line_vec / np.sqrt(np.sum(line_vec ** 2))
    vec_from_first = all_coords - first_point
    tiled_line_vec_norm = np.tile(line_vec_norm, (num_points, 1))
    scalar_product = np.sum(vec_from_first * tiled_line_vec_norm, axis=1)
    vec_from_first_parallel = np.outer(scalar_product, line_vec_norm)
    vec_to_line = vec_from_first - vec_from_first_parallel
    dist_to_line = np.sqrt(np.sum(vec_to_line ** 2, axis=1))
    tradeoff_idx = np.argmax(dist_to_line)
    return tradeoff_idx


def zstar_value(conf_level=.95):
    """
    References:
        http://stackoverflow.com/questions/28242593/correct-way-to-obtain-confidence-interval-with-scipy
    """
    import scipy.stats as spstats
    #distribution =
    #spstats.t.interval(.95, df=(ss - 1))[1]
    #spstats.norm.interval(.95, df=1)[1]
    zstar = spstats.norm.interval(conf_level)[1]
    #zstar = spstats.norm.ppf(spstats.norm.cdf(0) + (conf_level / 2))
    return zstar


def calc_error_bars_from_sample(sample_size, num_positive, pop, conf_level=.95):
    """
    Determines a error bars of sample

    References:
        https://www.qualtrics.com/blog/determining-sample-size/
        http://www.surveysystem.com/sscalc.htm
        https://en.wikipedia.org/wiki/Sample_size_determination
        http://www.surveysystem.com/sample-size-formula.htm
        http://courses.wcupa.edu/rbove/Berenson/10th%20ed%20CD-ROM%20topics/section8_7.pdf
        https://en.wikipedia.org/wiki/Standard_normal_table
        https://www.unc.edu/~rls/s151-2010/class23.pdf
    """
    #zValC_lookup = {.95: 3.8416, .99: 6.6564,}
    # We sampled ss from a population of pop and got num_positive true cases.
    ss = sample_size
    # Calculate at this confidence level
    zval = zstar_value(conf_level)
    # Calculate our plus/minus error in positive percentage
    pos_frac = (num_positive / ss)
    pf = (pop - ss) / (pop - 1)
    err_frac = zval * np.sqrt((pos_frac) * (1 - pos_frac) * pf / ss)
    lines = []
    lines.append('population_size = %r' % (pop,))
    lines.append('sample_size = %r' % (ss,))
    lines.append('num_positive = %r' % (num_positive,))
    lines.append('positive rate is %.2f%% ± %.2f%% @ %r confidence' % (
        100 * pos_frac, 100 * err_frac, conf_level))
    lines.append('positive num is %d ± %d @ %r confidence' % (
        int(np.round(pop * pos_frac)), int(np.round(pop * err_frac)), conf_level))
    print(ut.msgblock('Calculate Sample Error Margin', '\n'.join(lines)))


def calc_sample_from_error_bars(err_frac, pop, conf_level=.95, prior=.5):
    """
    Determines a reasonable sample size to achieve desired error bars.

    import sympy
    p, n, N, z = sympy.symbols('prior, ss, pop, zval')
    me = sympy.symbols('err_frac')
    expr = (z * sympy.sqrt((p * (1 - p) / n) * ((N - n) / (N - 1))))
    equation = sympy.Eq(me, expr)
    nexpr = sympy.solve(equation, [n])[0]
    nexpr = sympy.simplify(nexpr)

    import autopep8
    print(autopep8.fix_lines(['ss = ' + str(nexpr)], autopep8._get_options({}, False)))

    ss = -pop * prior* (zval**2) *(prior - 1) / ((err_frac ** 2) * pop - (err_frac**2) - prior * (zval**2) * (prior - 1))
    ss = pop * prior * zval ** 2 * (prior - 1) / (-err_frac ** 2 * pop + err_frac ** 2 + prior * zval ** 2 * (prior - 1))
    """
    # How much confidence ydo you want (in fraction of positive results)
    #zVal_lookup = {.95: 1.96, .99: 2.58,}
    zval = zstar_value(conf_level)

    std = .5
    zval * std * (1 - std) / err_frac

    #margin_error = err_frac
    #margin_error = zval * np.sqrt(prior * (1 - prior) / ss)

    #margin_error_small = zval * np.sqrt((prior * (1 - prior) / ss) * ((pop - ss) / (pop - 1)))
    #prior = .5  # initial uncertainty

    # Used for large samples
    #ss_large = (prior * (1 - prior)) / ((margin_error / zval) ** 2)

    # Used for small samples
    ss_numer = pop * prior * zval ** 2 * (1 - prior)
    ss_denom = (err_frac ** 2 * pop + err_frac ** 2 + prior * zval ** 2 * (1 - prior))
    ss_small = ss_numer / ss_denom

    #ss_ = ((zval ** 2) * 0.25) / (err_frac ** 2)
    #ss = int(np.ceil(ss_ / (1 + ((ss_ - 1) / pop))))
    ss = int(np.ceil(ss_small))
    lines = []
    lines.append('population_size = %r' % (pop,))
    lines.append('positive_prior = %r' % (prior,))
    lines.append('Desired confidence = %.2f' % (conf_level,))
    lines.append('Desired error rate is %.2f%%' % (err_frac * 100))
    lines.append('Desired number of errors is %d' % (int(round(err_frac * pop))))
    lines.append('Need sample sample size of %r to achive requirements' % (ss,))
    print(ut.msgblock('Calculate Required Sample Size', '\n'.join(lines)))


def inbounds(num, low, high, eq=False):
    r"""
    Args:
        num (scalar or ndarray):
        low (scalar or ndarray):
        high (scalar or ndarray):
        eq (bool):

    Returns:
        scalar or ndarray: is_inbounds

    CommandLine:
        xdoctest -m ~/code/vtool_ibeis/vtool_ibeis/other.py inbounds

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> import utool as ut
        >>> num = np.array([[ 0.   ,  0.431,  0.279],
        ...                 [ 0.204,  0.352,  0.08 ],
        ...                 [ 0.107,  0.325,  0.179]])
        >>> low  = .1
        >>> high = .4
        >>> eq = False
        >>> is_inbounds = inbounds(num, low, high, eq)
        >>> result = ub.repr2(is_inbounds, with_dtype=True)
        >>> print(result)

    """
    import operator as op
    less    = op.le if eq else op.lt
    greater = op.ge if eq else op.gt
    and_ = np.logical_and if isinstance(num, np.ndarray) else op.and_
    is_inbounds = and_(greater(num, low), less(num, high))
    return is_inbounds


def fromiter_nd(iter_, shape, dtype):
    """
    Like np.fromiter but handles iterators that generated
    n-dimensional arrays. Slightly faster than np.array.

    maybe commit to numpy?

    Args:
        iter_ (iter): an iterable that generates homogenous ndarrays
        shape (tuple): the expected output shape
        dtype (dtype): the numpy datatype of the generated ndarrays

    Note:
        The iterable must yeild a numpy array. It cannot yeild a Python list.

    CommandLine:
        python -m vtool_ibeis.other fromiter_nd --show

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> dtype = float
        >>> total = 11
        >>> rng = np.random.RandomState(0)
        >>> iter_ = (rng.rand(5, 7, 3) for _ in range(total))
        >>> shape = (total, 5, 7, 3)
        >>> result = fromiter_nd(iter_, shape, dtype)
        >>> assert result.shape == shape

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool_ibeis.other import *  # NOQA
        >>> dtype = int
        >>> qfxs = np.array([1, 2, 3])
        >>> dfxs = np.array([4, 5, 6])
        >>> iter_ = (np.array(x) for x in ut.product(qfxs, dfxs))
        >>> total = len(qfxs) * len(dfxs)
        >>> shape = (total, 2)
        >>> result = fromiter_nd(iter_, shape, dtype)
        >>> assert result.shape == shape
    """
    num_rows = shape[0]
    chunksize = np.prod(shape[1:])
    itemsize = np.dtype(dtype).itemsize
    # Create dtype that makes an entire ndarray appear as a single item
    chunk_dtype = np.dtype((np.void, itemsize * chunksize))
    arr = np.fromiter(iter_, count=num_rows, dtype=chunk_dtype)
    # Convert back to original dtype and shape
    arr = arr.view(dtype)
    arr.shape = shape
    return arr


def make_video2(images, outdir):
    import vtool_ibeis as vt
    from os.path import join
    n = str(int(np.ceil(np.log10(len(images)))))
    fmt = 'frame_%0' + n + 'd.png'
    ub.ensuredir(outdir)
    for count, img in enumerate(images):
        fname = join(outdir, fmt % (count))
        vt.imwrite(fname, img)


def make_video(images, outvid=None, fps=5, size=None,
               is_color=True, format='XVID'):
    """
    Create a video from a list of images.

    References:
        http://www.xavierdupre.fr/blog/2016-03-30_nojs.html
        http://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_gui/py_video_display/py_video_display.html

    @param      outvid      output video
    @param      images      list of images to use in the video
    @param      fps         frame per second
    @param      size        size of each frame
    @param      is_color    color
    @param      format      see http://www.fourcc.org/codecs.php

    The function relies on http://opencv-python-tutroals.readthedocs.org/en/latest/.
    By default, the video will have the size of the first image.
    It will resize every image to this size before adding them to the video.
    """
    # format = 'MJPG'
    # format = 'FMP4'
    import cv2
    fourcc = cv2.VideoWriter_fourcc(*str(format))
    vid = None
    for img in images:
        if vid is None:
            if size is None:
                size = img.shape[1], img.shape[0]
            vid = cv2.VideoWriter(outvid, fourcc, float(fps), size, is_color)
        if size[0] != img.shape[1] and size[1] != img.shape[0]:
            img = cv2.resize(img, size)
        vid.write(img)
    vid.release()
    return vid


def take_col_per_row(arr, colx_list):
    """ takes a column from each row

    Ignore:
        num_rows = 1000
        num_cols = 4

        arr = np.arange(10 * 4).reshape(10, 4)
        colx_list = (np.random.rand(10) * 4).astype(int)

        %timeit np.array([row[cx] for (row, cx) in zip(arr, colx_list)])
        %timeit arr.ravel().take(np.ravel_multi_index((np.arange(len(colx_list)), colx_list), arr.shape))
        %timeit arr.ravel().take(colx_list + np.arange(arr.shape[0]) * arr.shape[1])
    """
    # out = np.array([row[cx] for (row, cx) in zip(arr, colx_list)])
    multix_list = np.ravel_multi_index((np.arange(len(colx_list)), colx_list), arr.shape)
    out = arr.ravel().take(multix_list)
    return out


if __name__ == '__main__':
    """
    CommandLine:
        xdoctest -m vtool_ibeis.other
    """
    import xdoctest
    xdoctest.doctest_module(__file__)
