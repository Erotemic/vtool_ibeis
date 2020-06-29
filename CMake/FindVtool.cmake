# ##############################################################################
# Find Vtool
#
# This sets the following variables: VTOOL_FOUND - True if vtool was found.
# VTOOL_INCLUDE_DIRS - Directories containing the vtool include files.
# VTOOL_LIBRARIES - Libraries needed to use vtool. VTOOL_DEFINITIONS - Compiler
# flags for vtool.

find_package(PkgConfig)
pkg_check_modules(PC_VTOOL vtool)
set(VTOOL_DEFINITIONS ${PC_VTOOL_CFLAGS_OTHER})

find_path(VTOOL_INCLUDE_DIR vtool/vtool.hpp HINTS ${PC_VTOOL_INCLUDEDIR}
                                                  ${PC_VTOOL_INCLUDE_DIRS})

find_library(VTOOL_LIBRARY vtool HINTS ${PC_VTOOL_LIBDIR}
                                       ${PC_VTOOL_LIBRARY_DIRS})

set(VTOOL_INCLUDE_DIRS ${VTOOL_INCLUDE_DIR})
set(VTOOL_LIBRARIES ${VTOOL_LIBRARY})

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(Vtool DEFAULT_MSG VTOOL_LIBRARY
                                  VTOOL_INCLUDE_DIR)

mark_as_advanced(VTOOL_LIBRARY VTOOL_INCLUDE_DIR)
