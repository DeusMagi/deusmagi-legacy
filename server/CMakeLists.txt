# The Atrinik server CMakeLists file.

project(atrinik-server C)
cmake_minimum_required(VERSION 3.2)
set(EXECUTABLE atrinik-server)
set(PACKAGE_NAME "Atrinik Server")

# Need Flex...
find_package(FLEX REQUIRED)

# libdl is required.
find_library(DL_LIBRARY dl)

if (NOT DL_LIBRARY AND NOT MINGW)
    message(FATAL_ERROR "Could not find dl library.")
endif ()

# Add our includes.
include_directories(src/http_server)
include_directories(src/include)
include_directories(src/random_maps)
include_directories(src/tests)
include_directories(src/types/monster/include)
include_directories(src/types/include)
include_directories(src)

# Scan for lexers.
set(LEXERS
    src/loaders/map_header.l
    src/loaders/object.l
    src/loaders/random_map.l)
set(LEXERS_OUT)

# Add command to parse the lexer files with flex.
foreach (name ${LEXERS})
    string(REPLACE ".l" "" name ${name})
    set(src "${name}.l")
    set(dst "${name}.c")
    string(REPLACE "src/loaders/" "" name ${name})
    flex_target(${name} "${PROJECT_SOURCE_DIR}/${src}" "${PROJECT_SOURCE_DIR}/${dst}" COMPILE_FLAGS "-Cfa -i --prefix yy_${name}")
    get_property(out VARIABLE PROPERTY FLEX_${name}_OUTPUTS)
    set(LEXERS_OUT ${LEXERS_OUT} ${out})
endforeach (name)

# Add sources.
include(src/cmake.txt)

# Check is used for unit tests, but is optional.
find_library(CHECK_LIBRARY check)

if (CHECK_LIBRARY)
    set(HAVE_CHECK true)
else ()
    message(STATUS "Could not find check library, unit tests will be disabled.")
endif ()

# GD is used for world maker, but like unit tests, is also optional.
find_library(GD_LIBRARY gd)

if (GD_LIBRARY)
    set(HAVE_WORLD_MAKER true)
else ()
    message(STATUS "Could not find gd library, world maker module will be disabled.")
endif ()

# Find unit test source files if check is installed.
if (CHECK_LIBRARY)
    set(SOURCES_CHECK
        src/tests/check.c
        src/tests/bugs/cursed_treasures.c
        src/tests/unit/commands/object.c
        src/tests/unit/server/arch.c
        src/tests/unit/server/attack.c
        src/tests/unit/server/ban.c
        src/tests/unit/server/bank.c
        src/tests/unit/server/cache.c
        src/tests/unit/server/object.c
        src/tests/unit/server/re_cmp.c
        src/tests/unit/server/shop.c
        src/tests/unit/toolkit/math.c
        src/tests/unit/toolkit/memory.c
        src/tests/unit/toolkit/packet.c
        src/tests/unit/toolkit/pbkdf2.c
        src/tests/unit/toolkit/shstr.c
        src/tests/unit/toolkit/string.c
        src/tests/unit/toolkit/stringbuffer.c
        src/tests/unit/types/light_apply.c
        src/tests/unit/types/sound_ambient.c)
endif ()

# Find the world maker files, if enabled.
if (HAVE_WORLD_MAKER)
    set(SOURCES_WORLD_MAKER
        src/modules/world_maker.c)
endif ()

# Compile the sources into an executable.
add_executable(${EXECUTABLE} ${SOURCES} ${LEXERS_OUT} ${SOURCES_CHECK} ${SOURCES_WORLD_MAKER})
target_link_libraries(${EXECUTABLE} atrinik-toolkit)
target_link_libraries(${EXECUTABLE} -Xlinker --allow-multiple-definition)

# Link libraries.
if (DL_LIBRARY)
    target_link_libraries(${EXECUTABLE} ${DL_LIBRARY})
endif ()

# Link check.
if (CHECK_LIBRARY)
    target_link_libraries(${EXECUTABLE} ${CHECK_LIBRARY})
    target_link_libraries(${EXECUTABLE} subunit)

    if (UNIX AND NOT APPLE)
        target_link_libraries(${EXECUTABLE} rt)
    endif ()
endif ()

# Link GD.
if (GD_LIBRARY)
    target_link_libraries(${EXECUTABLE} ${GD_LIBRARY})

    if (MINGW)
        target_link_libraries(${EXECUTABLE} png)
    endif ()
endif ()

# Get all the include directories used to compile the server.
get_directory_property(INCLUDES INCLUDE_DIRECTORIES)

# Go through the include directories and construct a string.
foreach (var ${INCLUDES})
    string(REPLACE "${CMAKE_CURRENT_SOURCE_DIR}/" "" var ${var})
    set(INCLUDES_STRING "${INCLUDES_STRING} -I${var}")
endforeach (var)

# Go through the source files and construct a string.
foreach (var ${SOURCES} ${LEXERS_OUT})
    string(REPLACE "${CMAKE_CURRENT_SOURCE_DIR}/" "" var ${var})
    set(SOURCES_STRING "${SOURCES_STRING};${var}")
endforeach (var)

add_custom_target(test
    COMMAND ${EXECUTABLE} --unit --logger_filter_stdout=-info,-devel || exit 5
    COMMAND ${EXECUTABLE} --plugin_unit || exit 5
    COMMENT "Executing unit tests..."
    VERBATIM
)

if (CHECK_LIBRARY)
    # Go through the source files and construct a string.
    foreach (var ${SOURCES_CHECK})
        string(REPLACE "${CMAKE_CURRENT_SOURCE_DIR}/" "" var ${var})
        set(SOURCES_CHECK_STRING "${SOURCES_CHECK_STRING};${var}")
    endforeach (var)

    # Create a 'proto' build target, which generates the proto.h file.
    add_custom_target(proto_unit
        cproto -ve -o src/tests/check_proto.h.bak -D__CPROTO__${INCLUDES_STRING}${SOURCES_CHECK_STRING}
        COMMAND cmake -E echo "#ifndef __CPROTO__" > src/tests/check_proto.h
        COMMAND sed -e "s/\"\" //g" < src/tests/check_proto.h.bak >> src/tests/check_proto.h
        COMMAND cmake -E echo "#endif" >> src/tests/check_proto.h
        COMMAND cmake -E remove -f src/tests/check_proto.h.bak
        COMMAND python3 src/toolkit/adjust_proto.py src/tests/check_proto.h || exit 5
        WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
        COMMENT "Generating unit test prototypes..."
        VERBATIM)
endif ()

# Create the Arena plugin.
set(SOURCES_PLUGIN_ARENA
    src/plugins/plugin_arena/plugin_arena.c)
add_library(plugin_arena MODULE ${SOURCES_PLUGIN_ARENA})

# Set the preferred order of Python versions to find.
set(Python_ADDITIONAL_VERSIONS 3.10)
set(CMAKE_USE_PYTHON_VERSION ${Python_ADDITIONAL_VERSIONS})
# And try to find Python.
find_package(PythonLibs)

# Create the Python plugin, if Python was found.
if (PYTHONLIBS_FOUND)
    include_directories(${PYTHON_INCLUDE_DIRS})
    include_directories(src/plugins/plugin_python/include)
    set(HAVE_PYTHON true)

    set(SOURCES_PLUGIN_PYTHON
        src/plugins/plugin_python/atrinik_archetype.c
        src/plugins/plugin_python/atrinik_map.c
        src/plugins/plugin_python/atrinik_object.c
        src/plugins/plugin_python/atrinik_party.c
        src/plugins/plugin_python/atrinik_player.c
        src/plugins/plugin_python/atrinik_region.c
        src/plugins/plugin_python/attr_list.c
        src/plugins/plugin_python/plugin_python.c)
    add_library(plugin_python MODULE ${SOURCES_PLUGIN_PYTHON})
    target_link_libraries(plugin_python ${PYTHON_LIBRARIES})
    target_link_libraries(plugin_python -Xlinker --allow-multiple-definition)
else ()
    message(STATUS "Python libs not found, Python plugin will not be built.")
endif ()

# Configure the .h file with the configuration options (size of long,
# package version, etc).
configure_file(src/include/cmake.h.def src/include/cmake.h)
configure_file(src/include/version.h.def src/include/version.h)
