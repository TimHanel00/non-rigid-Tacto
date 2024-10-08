# This file will be configured to contain variables for CPack. These variables
# should be set in the CMake list file of the project before CPack module is
# included. The list of available CPACK_xxx variables and their associated
# documentation may be obtained using
#  cpack --help-variable-list
#
# Some variables are common to all generators (e.g. CPACK_PACKAGE_NAME)
# and some are specific to a generator
# (e.g. CPACK_NSIS_EXTRA_INSTALL_COMMANDS). The generator specific variables
# usually begin with CPACK_<GENNAME>_xxxx.


set(CPACK_BUILD_SOURCE_DIRS "/home/tim/extended_space/robot_learning/stlib;/home/tim/extended_space/robot_learning/stlib/build")
set(CPACK_CMAKE_GENERATOR "Unix Makefiles")
set(CPACK_COMPONENTS_ALL "Unspecified;applications;headers;libraries")
set(CPACK_COMPONENT_UNSPECIFIED_HIDDEN "TRUE")
set(CPACK_COMPONENT_UNSPECIFIED_REQUIRED "TRUE")
set(CPACK_DEFAULT_PACKAGE_DESCRIPTION_FILE "/usr/share/cmake-3.22/Templates/CPack.GenericDescription.txt")
set(CPACK_DEFAULT_PACKAGE_DESCRIPTION_SUMMARY "STLIB built using CMake")
set(CPACK_GENERATOR "ZIP")
set(CPACK_INSTALL_CMAKE_PROJECTS "/home/tim/extended_space/robot_learning/stlib/build;STLIB;ALL;/")
set(CPACK_INSTALL_PREFIX "/home/tim/extended_space/robot_learning/stlib/build/install/STLIB")
set(CPACK_MODULE_PATH "/home/tim/extended_space/robot_learning/stlib/cmake;/home/tim/extended_space/robot_learning/stlib/cmake/Modules;/home/tim/Sofa/SOFA_v22.12.00_Linux/lib/cmake/Sofa.Config;/home/tim/Sofa/SOFA_v22.12.00_Linux/lib/cmake/Modules")
set(CPACK_NSIS_DISPLAY_NAME "SOFA/v3.0/plugins/STLIB")
set(CPACK_NSIS_INSTALLER_ICON_CODE "")
set(CPACK_NSIS_INSTALLER_MUI_ICON_CODE "")
set(CPACK_NSIS_INSTALL_ROOT "$PROGRAMFILES")
set(CPACK_NSIS_PACKAGE_NAME "SOFA/v3.0/plugins/STLIB")
set(CPACK_NSIS_UNINSTALL_NAME "Uninstall")
set(CPACK_OUTPUT_CONFIG_FILE "/home/tim/extended_space/robot_learning/stlib/build/CPackConfig.cmake")
set(CPACK_PACKAGE_CONTACT "https://project.inria.fr/softrobot/contact/")
set(CPACK_PACKAGE_DEFAULT_LOCATION "/")
set(CPACK_PACKAGE_DESCRIPTION "Ease the modeling, the simulation and the control of soft-robots in SOFA.")
set(CPACK_PACKAGE_DESCRIPTION_FILE "/home/tim/extended_space/robot_learning/stlib/README.md")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "STLIB built using CMake")
set(CPACK_PACKAGE_FILE_NAME "STLIB_v3.0_Linux")
set(CPACK_PACKAGE_HOMEPAGE_URL "https://project.inria.fr/softrobot")
set(CPACK_PACKAGE_INSTALL_DIRECTORY "SOFA/v3.0/plugins/STLIB")
set(CPACK_PACKAGE_INSTALL_REGISTRY_KEY "SOFA/v3.0/plugins/STLIB")
set(CPACK_PACKAGE_NAME "STLIB v3.0")
set(CPACK_PACKAGE_RELOCATABLE "true")
set(CPACK_PACKAGE_VENDOR "Defrost team")
set(CPACK_PACKAGE_VERSION "3.0")
set(CPACK_PACKAGE_VERSION_MAJOR "3")
set(CPACK_PACKAGE_VERSION_MINOR "0")
set(CPACK_RESOURCE_FILE_LICENSE "/home/tim/extended_space/robot_learning/stlib/LICENSE")
set(CPACK_RESOURCE_FILE_README "/home/tim/extended_space/robot_learning/stlib/README.md")
set(CPACK_RESOURCE_FILE_WELCOME "/home/tim/extended_space/robot_learning/stlib/README.md")
set(CPACK_SET_DESTDIR "OFF")
set(CPACK_SOURCE_GENERATOR "TBZ2;TGZ;TXZ;TZ")
set(CPACK_SOURCE_OUTPUT_CONFIG_FILE "/home/tim/extended_space/robot_learning/stlib/build/CPackSourceConfig.cmake")
set(CPACK_SOURCE_RPM "OFF")
set(CPACK_SOURCE_TBZ2 "ON")
set(CPACK_SOURCE_TGZ "ON")
set(CPACK_SOURCE_TXZ "ON")
set(CPACK_SOURCE_TZ "ON")
set(CPACK_SOURCE_ZIP "OFF")
set(CPACK_SYSTEM_NAME "Linux")
set(CPACK_THREADS "1")
set(CPACK_TOPLEVEL_TAG "Linux")
set(CPACK_WIX_SIZEOF_VOID_P "8")

if(NOT CPACK_PROPERTIES_FILE)
  set(CPACK_PROPERTIES_FILE "/home/tim/extended_space/robot_learning/stlib/build/CPackProperties.cmake")
endif()

if(EXISTS ${CPACK_PROPERTIES_FILE})
  include(${CPACK_PROPERTIES_FILE})
endif()
