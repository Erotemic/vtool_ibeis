# -*- coding: utf-8 -*-
# LICENCE
from __future__ import absolute_import, division, print_function
import numpy as np
from .util_math import TAU


def atan2(y, x):
    """
    does atan2 but returns from 0 to TAU

    Example:
        >>> from vtool.trig import *  # NOQA
        >>> import utool
        >>> rng = np.random.RandomState(0)
        >>> y = rng.rand(1000).astype(np.float64)
        >>> x = rng.rand(1000).astype(np.float64)
        >>> theta = atan2(y, x)
        >>> assert np.all(theta >= 0)
        >>> assert np.all(theta < 2 * np.pi)
        >>> import ubelt as ub
        >>> print(ub.hash_data(theta))
        6bfc86a2e94dd2dafbf501035719a7873d57f5f8e9cde88c4ccc35e98bb9e7b82abf6230803a923be7060866d66b8ac567388803593f9b7c763163a24282442a
    """
    theta = np.arctan2(y, x)  # outputs from -TAU/2 to TAU/2
    theta[theta < 0] = theta[theta < 0] + TAU  # map to 0 to TAU (keep coords)
    return theta
