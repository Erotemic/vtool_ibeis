macro(GET_OS_INFO)
  string(REGEX MATCH "Linux" OS_IS_LINUX ${CMAKE_SYSTEM_NAME})
  string(REGEX MATCH "Darwin" OS_IS_MACOS ${CMAKE_SYSTEM_NAME})
  set(SVER_LIB_INSTALL_DIR "lib${LIB_SUFFIX}")
  set(SVER_INCLUDE_INSTALL_DIR
      "include/${PROJECT_NAME_LOWER}-${VTOOL_VERSION_MAJOR}.${VTOOL_VERSION_MINOR}"
  )
endmacro(GET_OS_INFO)

macro(DISSECT_VERSION)
  # Find version components
  message(STATUS "VTOOL_VERSION = ${VTOOL_VERSION}")
  string(REGEX REPLACE "^([0-9]+).*" "\\1" VTOOL_VERSION_MAJOR
                       "${VTOOL_VERSION}")
  string(REGEX REPLACE "^[0-9]+\\.([0-9]+).*" "\\1" VTOOL_VERSION_MINOR
                       "${VTOOL_VERSION}")
  string(REGEX REPLACE "^[0-9]+\\.[0-9]+\\.([0-9]+)" "\\1" VTOOL_VERSION_PATCH
                       ${VTOOL_VERSION})
  string(REGEX REPLACE "^[0-9]+\\.[0-9]+\\.[0-9]+(.*)" "\\1"
                       VTOOL_VERSION_CANDIDATE ${VTOOL_VERSION})
  set(VTOOL_SOVERSION "${VTOOL_VERSION_MAJOR}.${VTOOL_VERSION_MINOR}")
  message(STATUS "VTOOL_SOVERSION = ${VTOOL_SOVERSION}")
endmacro(DISSECT_VERSION)

macro(vtool_add_pyunit file)
  # find test file
  set(_file_name _file_name-NOTFOUND)
  find_file(_file_name ${file} ${CMAKE_CURRENT_SOURCE_DIR})
  if(NOT _file_name)
    message(FATAL_ERROR "Can't find pyunit file \"${file}\"")
  endif(NOT _file_name)

  # add target for running test
  string(REPLACE "/" "_" _testname ${file})
  add_custom_target(
    pyunit_${_testname}
    COMMAND ${PYTHON_EXECUTABLE} ${PROJECT_SOURCE_DIR}/bin/run_test.py
            ${_file_name}
    DEPENDS ${_file_name}
    WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/test
    VERBATIM
    COMMENT "Running pyunit test(s) ${file}")
  # add dependency to 'test' target
  add_dependencies(pyunit_${_testname} vtool)
  add_dependencies(test pyunit_${_testname})
endmacro(vtool_add_pyunit)
