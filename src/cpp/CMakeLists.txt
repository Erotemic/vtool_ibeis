# include_directories(${CMAKE_SOURCE_DIR}/include algorithms ext util nn .)

message(STATUS "VTOOL_VERSION = ${VTOOL_VERSION}")
set(SVER_VERSION ${VTOOL_VERSION})
message(STATUS "SVER_VERSION = ${SVER_VERSION}")
add_definitions(-D_VTOOL_VERSION=${VTOOL_VERSION})
add_definitions(-DVTOOL_VERSION_=${VTOOL_VERSION})
add_definitions(-DVTOOL_VERSION=${VTOOL_VERSION})
add_definitions(-D_SVER_VERSION=${SVER_VERSION})
add_definitions(-DSVER_VERSION_=${SVER_VERSION})
add_definitions(-DSVER_VERSION=${SVER_VERSION})

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/sver/config.h.in
               ${CMAKE_CURRENT_SOURCE_DIR}/sver/config.h)

file(GLOB_RECURSE CPP_SOURCES sver.cpp)

add_library(sver_s STATIC ${CPP_SOURCES})
target_link_libraries(sver_s ${OpenCV_LIBS})

if(CMAKE_COMPILER_IS_GNUCC OR CMAKE_COMPILER_IS_CLANG)
  set_target_properties(sver_s PROPERTIES COMPILE_FLAGS -fPIC)
endif()

set_property(TARGET sver_s PROPERTY COMPILE_DEFINITIONS SVER_STATIC)

add_library(sver SHARED "${CMAKE_CURRENT_SOURCE_DIR}/sver/sver.h")

if(OS_IS_LINUX)
  set_target_properties(sver PROPERTIES LINKER_LANGUAGE CXX)
  set(LINK_FLAG_PREFIX "-Wl,--whole-archive")
  set(LINK_FLAG_POSTFIX "-Wl,--no-whole-archive")
elseif(OS_IS_MACOS)
  set(LINK_FLAG_PREFIX "-Wl,-all_load")
else()
  set_target_properties(sver PROPERTIES WINDOWS_EXPORT_ALL_SYMBOLS YES)
  set(LINK_FLAG_PREFIX "/WHOLEARCHIVE")
endif()

target_link_libraries(sver ${LINK_FLAG_PREFIX} sver_s ${LINK_FLAG_POSTFIX})

set_target_properties(
  sver PROPERTIES VERSION ${VTOOL_VERSION} SOVERSION ${VTOOL_SOVERSION}
                  DEFINE_SYMBOL VTOOL_EXPORTS)

if(NOT SKBUILD)
  install(
    TARGETS sver sver_s
    EXPORT ${targets_export_name}
    INCLUDES
    DESTINATION include
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION ${SVER_LIB_INSTALL_DIR}
    ARCHIVE DESTINATION ${SVER_LIB_INSTALL_DIR})

  install(
    DIRECTORY sver
    DESTINATION include
    FILES_MATCHING
    PATTERN "*.h"
    PATTERN "*.hpp")

else()
  # Only install the library files when building with skbuild
  install(
    TARGETS sver sver_s
    EXPORT ${targets_export_name}
    LIBRARY DESTINATION ${SVER_LIB_INSTALL_DIR}
    ARCHIVE DESTINATION ${SVER_LIB_INSTALL_DIR})
endif()
