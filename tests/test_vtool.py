# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from six.moves import range
import vtool.keypoint as ktool
import vtool.linalg as ltool
import numpy as np
import utool as ut
from vtool import demodata
from vtool.util_math import TAU


def test_get_invR_mats_orientation():
    theta1 = TAU / 8
    theta2 = -TAU / 8
    theta3 = 0
    theta4 = 7 * TAU / 8

    invV_mats = demodata.get_dummy_invV_mats()

    def R_mats(theta):
        return np.array([ltool.rotation_mat2x2(theta) for _ in range(len(invV_mats))])

    def test_rots(theta):
        invVR_mats = np.matmul(invV_mats, R_mats(theta))
        _oris = ktool.get_invVR_mats_oris(invVR_mats)
        print('________')
        print('theta = %r' % (theta % TAU,))
        print('b / a = %r' % (_oris,))
        passed, error = ut.almost_eq(_oris, theta % TAU, ret_error=True)
        try:
            assert np.all(passed)
        except AssertionError as ex:
            ut.printex(ex, 'rotation unequal', key_list=['passed', 'error'])

    test_rots(theta1)
    test_rots(theta2)
    test_rots(theta3)
    test_rots(theta4)


if __name__ == '__main__':
    test_get_invR_mats_orientation()
