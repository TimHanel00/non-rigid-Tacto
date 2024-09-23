# Install script for directory: /home/tim/extended_space/robot_learning/stlib

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/home/tim/extended_space/robot_learning/stlib/build/install/STLIB")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Release")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xheadersx" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/STLIB/STLIBTargets.cmake")
    file(DIFFERENT EXPORT_FILE_CHANGED FILES
         "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/STLIB/STLIBTargets.cmake"
         "/home/tim/extended_space/robot_learning/stlib/build/CMakeFiles/Export/lib/cmake/STLIB/STLIBTargets.cmake")
    if(EXPORT_FILE_CHANGED)
      file(GLOB OLD_CONFIG_FILES "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/STLIB/STLIBTargets-*.cmake")
      if(OLD_CONFIG_FILES)
        message(STATUS "Old export file \"$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/STLIB/STLIBTargets.cmake\" will be replaced.  Removing files [${OLD_CONFIG_FILES}].")
        file(REMOVE ${OLD_CONFIG_FILES})
      endif()
    endif()
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/STLIB" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/CMakeFiles/Export/lib/cmake/STLIB/STLIBTargets.cmake")
  if("${CMAKE_INSTALL_CONFIG_NAME}" MATCHES "^([Rr][Ee][Ll][Ee][Aa][Ss][Ee])$")
    file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/STLIB" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/CMakeFiles/Export/lib/cmake/STLIB/STLIBTargets-release.cmake")
  endif()
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xheadersx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/STLIB" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/STLIBConfigVersion.cmake")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xheadersx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/STLIB" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/cmake/STLIBConfig.cmake")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xresourcesx" OR NOT CMAKE_INSTALL_COMPONENT)
  
        find_package(Git REQUIRED)
        # get the current commit sha
        execute_process(
            COMMAND ${GIT_EXECUTABLE} rev-parse HEAD
            WORKING_DIRECTORY "/home/tim/extended_space/robot_learning/stlib"
            OUTPUT_VARIABLE CURRENT_GIT_COMMIT
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        # get the branches containing current commit
        execute_process(
            COMMAND ${GIT_EXECUTABLE} branch -a --contains "${CURRENT_GIT_COMMIT}"
            WORKING_DIRECTORY "/home/tim/extended_space/robot_learning/stlib"
            OUTPUT_VARIABLE CURRENT_GIT_BRANCH
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        # get the current remotes
        execute_process(
            COMMAND ${GIT_EXECUTABLE} remote -vv
            WORKING_DIRECTORY "/home/tim/extended_space/robot_learning/stlib"
            OUTPUT_VARIABLE CURRENT_GIT_REMOTE
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        # get more info (hash, author, date, comment)
        execute_process(
            COMMAND ${GIT_EXECUTABLE} log --pretty -n 1
            WORKING_DIRECTORY "/home/tim/extended_space/robot_learning/stlib"
            OUTPUT_VARIABLE CURRENT_GIT_INFO
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        # write all info in git-info.txt
        file(WRITE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/git-info.txt"
            "# Git info for STLIB"                              \n
                                                                    \n
            "## Current commit"                                   \n
            "## git rev-parse --abbrev-ref HEAD"                  \n
            "${CURRENT_GIT_COMMIT}"                              \n
                                                                    \n
            "## Branches containing current commit"               \n
            "## git branch -a --contains ${CURRENT_GIT_COMMIT} " \n
            "${CURRENT_GIT_BRANCH}"                              \n
                                                                    \n
            "## Remotes"                                          \n
            "## git remote -vv "                                  \n
            "${CURRENT_GIT_REMOTE}"                              \n
                                                                    \n
            "## More info"                                        \n
            "## git log --pretty -n 1"                            \n
            "${CURRENT_GIT_INFO}"                                \n
            )
        
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xlibrariesx" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSTLIB.so.3.0" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSTLIB.so.3.0")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSTLIB.so.3.0"
         RPATH "$ORIGIN/../lib:$$ORIGIN/../lib:$ORIGIN/../../../collections/SofaCore/lib:$$ORIGIN/../../../collections/SofaCore/lib:@loader_path/../../../collections/SofaCore/lib:@executable_path/../../../collections/SofaCore/lib:$ORIGIN/../../../lib:$$ORIGIN/../../../lib:@loader_path/../../../lib:@executable_path/../../../lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/libSTLIB.so.3.0")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSTLIB.so.3.0" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSTLIB.so.3.0")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSTLIB.so.3.0"
         OLD_RPATH "/home/tim/Sofa/SOFA_v22.12.00_Linux/collections/SofaCore/lib:/home/tim/Sofa/SOFA_v22.12.00_Linux/lib::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::"
         NEW_RPATH "$ORIGIN/../lib:$$ORIGIN/../lib:$ORIGIN/../../../collections/SofaCore/lib:$$ORIGIN/../../../collections/SofaCore/lib:@loader_path/../../../collections/SofaCore/lib:@executable_path/../../../collections/SofaCore/lib:$ORIGIN/../../../lib:$$ORIGIN/../../../lib:@loader_path/../../../lib:@executable_path/../../../lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSTLIB.so.3.0")
    endif()
  endif()
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xlibrariesx" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSTLIB.so" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSTLIB.so")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSTLIB.so"
         RPATH "$ORIGIN/../lib:$$ORIGIN/../lib:$ORIGIN/../../../collections/SofaCore/lib:$$ORIGIN/../../../collections/SofaCore/lib:@loader_path/../../../collections/SofaCore/lib:@executable_path/../../../collections/SofaCore/lib:$ORIGIN/../../../lib:$$ORIGIN/../../../lib:@loader_path/../../../lib:@executable_path/../../../lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/libSTLIB.so")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSTLIB.so" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSTLIB.so")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSTLIB.so"
         OLD_RPATH "/home/tim/Sofa/SOFA_v22.12.00_Linux/collections/SofaCore/lib:/home/tim/Sofa/SOFA_v22.12.00_Linux/lib::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::"
         NEW_RPATH "$ORIGIN/../lib:$$ORIGIN/../lib:$ORIGIN/../../../collections/SofaCore/lib:$$ORIGIN/../../../collections/SofaCore/lib:@loader_path/../../../collections/SofaCore/lib:@executable_path/../../../collections/SofaCore/lib:$ORIGIN/../../../lib:$$ORIGIN/../../../lib:@loader_path/../../../lib:@executable_path/../../../lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSTLIB.so")
    endif()
  endif()
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xheadersx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/STLIB" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/src/initPlugin.h")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xheadersx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/." TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/README.md")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/sofa/STLIB" TYPE DIRECTORY FILES "/home/tim/extended_space/robot_learning/stlib/docs")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/." TYPE FILE FILES
    "/home/tim/extended_space/robot_learning/stlib/README.md"
    "/home/tim/extended_space/robot_learning/stlib/LICENSE"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/algorithms" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/algorithms/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/animation" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/animation/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/animation" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/animation/animate.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/animation" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/animation/easing.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/caching" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/caching/cacher.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/constants" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/constants/Key.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/constants" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/constants/KeyCode.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/constants" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/constants/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/debug" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/debug/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/geometric" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/geometric/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/geometric/data/meshes" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/geometric/data/meshes/parametric_mesh_example.step")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/geometric" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/geometric/gmsh.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/loaders" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/loaders/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/numerics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/numerics/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/numerics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/numerics/matrix.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/numerics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/numerics/matrix_test.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/numerics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/numerics/quat.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/numerics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/numerics/quat_test.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/numerics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/numerics/vec3.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/numerics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/numerics/vec3_test.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/objectmodel" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/objectmodel/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/scenegraph" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/scenegraph/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/units" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/units/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/units" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/units/material.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/units" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/units/time.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib/units" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/units/units.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/splib" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/splib/utils.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/algorithms" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/algorithms/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/animation" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/animation/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/communication" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/communication/UDP_controller.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/components" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/components/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/components" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/components/all.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/debug" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/debug/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/loader" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/loader/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/loader/mesh" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/loader/mesh/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/loader/mesh/parametricmeshloader" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/loader/mesh/parametricmeshloader/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/loader/mesh/parametricmeshloader" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/loader/mesh/parametricmeshloader/parametricmeshloader.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/numerics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/numerics/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/physics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/physics/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/physics/collision" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/physics/collision/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/physics/collision" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/physics/collision/collision.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/physics/constraints" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/physics/constraints/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/physics/constraints" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/physics/constraints/fixedbox.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/physics/constraints" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/physics/constraints/partiallyfixedbox.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/physics/constraints" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/physics/constraints/subTopology.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/physics/deformable" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/physics/deformable/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/physics/deformable" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/physics/deformable/elasticmaterialobject.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/physics/mixedmaterial" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/physics/mixedmaterial/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/physics/mixedmaterial" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/physics/mixedmaterial/rigidification.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/physics/rigid" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/physics/rigid/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/physics/rigid" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/physics/rigid/rigidobject.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/scene" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/scene/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/scene" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/scene/contactheader.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/scene" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/scene/interaction.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/scene" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/scene/mainheader.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/scene" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/scene/wrapper.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/solver" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/solver/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/solver" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/solver/defaultsolver.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/tools" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/tools/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/units" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/units/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/stlib/visuals" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/stlib/visuals/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/python/test" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/python/test/TestExampleScenes.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xapplicationsx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/etc/sofa/python.d" TYPE FILE RENAME "STLIB" FILES "/home/tim/extended_space/robot_learning/stlib/build/installed-SofaPython-config")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/algorithms" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/algorithms/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/animation" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/animation/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/animation" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/animation/animate.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/animation" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/animation/easing.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/constants" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/constants/Key.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/constants" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/constants/KeyCode.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/constants" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/constants/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/debug" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/debug/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/geometric" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/geometric/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/geometric/data/meshes" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/geometric/data/meshes/CapNoCavities.brep")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/geometric" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/geometric/gmesh.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/loader" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/loader/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/loaders" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/loaders/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/numerics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/numerics/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/numerics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/numerics/matrix.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/numerics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/numerics/matrix_test.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/numerics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/numerics/quat.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/numerics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/numerics/quat_test.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/numerics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/numerics/vec3.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/numerics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/numerics/vec3_test.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/objectmodel" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/objectmodel/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/scenegraph" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/scenegraph/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/units" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/units/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/units" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/units/material.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/units" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/units/time.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3/units" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/units/units.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/splib3" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/splib3/utils.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/communication" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/communication/UDP_controller.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/components" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/components/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/components" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/components/all.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/debug" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/debug/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/numerics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/numerics/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/physics" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/physics/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/physics/collision" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/physics/collision/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/physics/collision" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/physics/collision/collision.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/physics/constraints" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/physics/constraints/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/physics/constraints" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/physics/constraints/fixedbox.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/physics/constraints" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/physics/constraints/fixedbox_prefab.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/physics/constraints" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/physics/constraints/partiallyfixedbox.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/physics/constraints" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/physics/constraints/subTopology.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/physics/deformable" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/physics/deformable/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/physics/deformable" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/physics/deformable/elasticmaterialobject.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/physics/mixedmaterial" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/physics/mixedmaterial/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/physics/mixedmaterial" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/physics/mixedmaterial/rigidification.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/physics/rigid" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/physics/rigid/RigidObject.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/physics/rigid" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/physics/rigid/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/scene" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/scene/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/scene" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/scene/contactheader.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/scene" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/scene/interaction.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/scene" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/scene/mainheader.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/scene" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/scene/scene.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/scene" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/scene/wrapper.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/solver" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/solver/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/solver" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/solver/defaultsolver.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/tools" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/tools/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/visuals" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/visuals/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/site-packages/stlib3/visuals" TYPE FILE FILES "/home/tim/extended_space/robot_learning/stlib/build/lib/python3/site-packages/stlib3/visuals/visualmodel.py")
endif()

if(CMAKE_INSTALL_COMPONENT)
  set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
file(WRITE "/home/tim/extended_space/robot_learning/stlib/build/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
