set(PKG_DESC "Image Tools for Wildbook IA")
set(pkg_conf_file ${CMAKE_CURRENT_BINARY_DIR}/vtool.pc)
configure_file(vtool.pc.in ${pkg_conf_file} @ONLY)
install(
  FILES ${pkg_conf_file}
  DESTINATION ${SVER_LIB_INSTALL_DIR}/pkgconfig/
  COMPONENT pkgconfig)
