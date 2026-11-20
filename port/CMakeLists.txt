# dsignition - ReXGlue Recompiled Project
#
# SDK boilerplate lives in generated/rexglue.cmake.

cmake_minimum_required(VERSION 3.25)
project(dsignition LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(generated/rexglue.cmake)

# Sources
set(DSIGNITION_SOURCES
    src/main.cpp
    src/dsi_hooks.cpp
)
if(WIN32)
    # exe icon; SDL also takes the game window / taskbar icon from it
    enable_language(RC)
    list(APPEND DSIGNITION_SOURCES res/dsignition.rc)
endif()

if(WIN32)
    add_executable(dsignition WIN32 ${DSIGNITION_SOURCES})
else()
    add_executable(dsignition ${DSIGNITION_SOURCES})
endif()

rexglue_setup_target(dsignition)
