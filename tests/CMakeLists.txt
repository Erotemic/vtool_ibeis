add_custom_target(tests)

add_dependencies(test tests)

set(EXECUTABLE_OUTPUT_PATH ${TEST_OUTPUT_PATH})

# ---------- pyunit tests --------------
if(BUILD_PYTHON_BINDINGS)
  vtool_add_pyunit(test_akmeans.py)
  vtool_add_pyunit(test_coverage_max_reduce.py)
  vtool_add_pyunit(test_draw_keypoint.py)
  vtool_add_pyunit(test_pyflann.py)
  vtool_add_pyunit(test_spatial_verification.py)
  vtool_add_pyunit(test_sver_wrapper.py)
  vtool_add_pyunit(test_vtool.py)
  vtool_add_pyunit(testdata_nondeterm_sver.py)
endif()
