cmake_minimum_required(VERSION 3.13.0)

set(CMAKE_CXX_STANDARD 11)

if(COMMAND cmake_policy)
  cmake_policy(SET CMP0003 NEW)
  cmake_policy(SET CMP0042 NEW)
endif(COMMAND cmake_policy)

project(vtool LANGUAGES C CXX)
string(TOLOWER ${PROJECT_NAME} PROJECT_NAME_LOWER)

include(${PROJECT_SOURCE_DIR}/CMake/vtool-utils.cmake)

function(_pycmd outvar cmd)
  execute_process(
    COMMAND python -c "${cmd}"
    RESULT_VARIABLE _exitcode
    OUTPUT_VARIABLE _output
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
  if(NOT ${_exitcode} EQUAL 0)
    message(ERROR "Failed when running python code: \"\"\"
${cmd}\"\"\"")
    message(FATAL_ERROR "Python command failed with error code: ${_exitcode}")
  endif()
  # Remove supurflous newlines (artifacts of print)
  string(STRIP "${_output}" _output)
  set(${outvar}
      "${_output}"
      PARENT_SCOPE)
endfunction()
_pycmd(VTOOL_VERSION "import setup; print(setup.version)")

message(STATUS "VTOOL_VERSION = ${VTOOL_VERSION}")

dissect_version()
get_os_info()

if(OS_IS_MACOS)
  message(STATUS "INCLUDING MACPORTS")

  include_directories(/opt/local/include)
  link_directories(/opt/local/lib)

  find_package(Eigen3 3 REQUIRED NO_MODULE)

  set(CMAKE_INSTALL_RPATH "/opt/local/lib")

  # Add flags to support clang2
  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -stdlib=libc++")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++")
  set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -lc++")
  set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -lc++")
endif()

# Setup basic python stuff and ensure we have skbuild list(INSERT
# CMAKE_MODULE_PATH 0 "${CMAKE_SOURCE_DIR}/CMake") include( skbuild-helpers )

# ##############################################################################

# detect if using the Clang compiler
if("${CMAKE_C_COMPILER_ID}" MATCHES "Clang")
  set(CMAKE_COMPILER_IS_CLANG 1)
endif()

if("${CMAKE_CXX_COMPILER_ID}" MATCHES "Clang")
  set(CMAKE_COMPILER_IS_CLANGXX 1)
endif()

list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/CMake)

# Add an "uninstall" target
configure_file("${PROJECT_SOURCE_DIR}/CMake/uninstall_target.cmake.in"
               "${PROJECT_BINARY_DIR}/uninstall_target.cmake" IMMEDIATE @ONLY)
add_custom_target(uninstall "${CMAKE_COMMAND}" -P
                            "${PROJECT_BINARY_DIR}/uninstall_target.cmake")

# Set the build type.  Options are: Debug          : w/ debug symbols, w/o
# optimization Release        : w/o debug symbols, w/ optimization
# RelWithDebInfo : w/ debug symbols, w/ optimization MinSizeRel     : w/o debug
# symbols, w/ optimization, stripped binaries

if(NOT CMAKE_BUILD_TYPE)
  # set(CMAKE_BUILD_TYPE Release)
  set(CMAKE_BUILD_TYPE
      RelWithDebInfo
      CACHE STRING "Build type" FORCE)
  # set(CMAKE_BUILD_TYPE Debug)
endif()

# set the default path for built executables to the "bin" directory
set(EXECUTABLE_OUTPUT_PATH ${PROJECT_BINARY_DIR}/bin)
# set the default path for built libraries to the "lib" directory
set(LIBRARY_OUTPUT_PATH ${PROJECT_BINARY_DIR}/lib)
# set output path for tests
set(TEST_OUTPUT_PATH ${PROJECT_SOURCE_DIR}/test)

option(BUILD_TESTS "Build tests" ON)
option(BUILD_DOC "Build documentation" ON)
option(USE_OPENMP "Use OpenMP multi-threading" ON)

if(OS_IS_MACOS)
  find_package(Gflags REQUIRED)
  if(Gflags_FOUND
     OR GFLAGS_FOUND
     OR GFLAGS_INCLUDE_DIRS)
    message(STATUS "GFLAGS_INCLUDE_DIR: ${GFLAGS_INCLUDE_DIR}")
    message(STATUS "GFLAGS_LIBRARIES: ${GFLAGS_LIBRARIES}")
    include_directories(${GFLAGS_INCLUDE_DIR})
  else()
    message(FATAL_ERROR "GFlags NOT found")
  endif()
endif()

find_package(OpenCV REQUIRED)
if(OpenCV_FOUND)
  include_directories(${OpenCV_INCLUDE_DIR})
else()
  message(FATAL_ERROR "OpenCV NOT found")
endif()

if(USE_OPENMP)
  find_package(OpenMP)
  if(OPENMP_FOUND)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
    set(CMAKE_EXE_LINKER_FLAGS
        "${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_EXE_LINKER_FLAGS}")
  else()
    message(WARNING "OpenMP NOT found")
  endif()
endif()

find_package(PkgConfig REQUIRED)

# set the C/C++ include path to the "include" directory
include_directories(BEFORE ${PROJECT_SOURCE_DIR}/src/cpp)

add_definitions("-Wall -Wno-unknown-pragmas -Wno-unused-function")

# install and export variables
set(config_install_dir "lib/CMake/${PROJECT_NAME}")
set(generated_dir "${CMAKE_CURRENT_BINARY_DIR}/generated")
set(version_config "${generated_dir}/vtool-config-version.cmake")
set(project_config "${generated_dir}/vtool-config.cmake")
set(targets_export_name "vtool-targets")
set(namespace "vtool::")

if(SKBUILD)
  # Override output paths when using scikit-build
  set(SVER_LIB_INSTALL_DIR "vtool/lib")
  set(SVER_INCLUDE_INSTALL_DIR "vtool/include")
endif()

if(NOT SKBUILD)
  add_subdirectory(CMake)
endif()
add_subdirectory(src/cpp)
if(BUILD_TESTS)
  add_subdirectory(test)
endif(BUILD_TESTS)

# CMake configuration file creation Include module with fuction
# 'write_basic_package_version_file'
include(CMakePackageConfigHelpers)

# Configure 'vtool-config-version.cmake' Note: VTOOL_VERSION is used as a
# VERSION
write_basic_package_version_file(
  "${version_config}"
  VERSION ${VTOOL_VERSION}
  COMPATIBILITY SameMajorVersion)

# Configure 'vtool-config.cmake' Use variables: * targets_export_name *
# PROJECT_NAME
configure_package_config_file("CMake/Config.cmake.in" "${project_config}"
                              INSTALL_DESTINATION "${config_install_dir}")

if(NOT SKBUILD)
  # Config * <prefix>/lib/CMake/vtool/vtool-config.cmake *
  # <prefix>/lib/CMake/vtool/vtool-config-version.cmake
  install(FILES "${project_config}" "${version_config}"
          DESTINATION "${config_install_dir}")
  # Config * <prefix>/lib/CMake/vtool/vtool-targets.cmake
  install(
    EXPORT "${targets_export_name}"
    NAMESPACE "${namespace}"
    DESTINATION "${config_install_dir}")
endif()

# CPACK options

# RPM
find_program(RPM_PROGRAM rpm)
if(EXISTS ${RPM_PROGRAM})
  list(APPEND CPACK_GENERATOR "RPM")
endif(EXISTS ${RPM_PROGRAM})
# DEB
find_program(DPKG_PROGRAM dpkg)
if(EXISTS ${DPKG_PROGRAM})
  list(APPEND CPACK_GENERATOR "DEB")
endif(EXISTS ${DPKG_PROGRAM})
# NSIS
find_program(NSIS_PROGRAM makensis MakeNSIS)
if(EXISTS ${NSIS_PROGRAM})
  list(APPEND CPACK_GENERATOR "NSIS")
endif(EXISTS ${NSIS_PROGRAM})
# dpkg
find_program(PACKAGE_MAKER_PROGRAM PackageMaker
             HINTS /Developer/Applications/Utilities)
if(EXISTS ${PACKAGE_MAKER_PROGRAM})
  list(APPEND CPACK_GENERATOR "PackageMaker")
endif(EXISTS ${PACKAGE_MAKER_PROGRAM})

set(CPACK_GENERATOR "${CPACK_GENERATOR}")
set(CPACK_MONOLITHIC_INSTALL 1)
set(CPACK_SET_DESTDIR ON)
include(InstallRequiredSystemLibraries)
set(CPACK_PACKAGE_CONTACT "Marius Muja")
set(CPACK_PACKAGING_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX})
set(CPACK_PACKAGE_VERSION ${VTOOL_VERSION})
set(CPACK_PACKAGE_VERSION_MAJOR ${VTOOL_VERSION_MAJOR})
set(CPACK_PACKAGE_VERSION_MINOR ${VTOOL_VERSION_MINOR})
set(CPACK_PACKAGE_VERSION_PATCH ${VTOOL_VERSION_PATCH})
include(CPack)

message(STATUS "Install prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "Building tests: ${BUILD_TESTS}")
message(STATUS "Building documentation: ${BUILD_DOC}")
message(STATUS "Using OpenMP support: ${USE_OPENMP}")
