# The Atrinik toolkit CMakeLists file.

project(atrinik-toolkit C)
cmake_minimum_required(VERSION 3.2)
set(ATRINIK_TOOLKIT atrinik-toolkit)

# cURL is required by the metaserver.
find_package(CURL REQUIRED)
include_directories(${CURL_INCLUDE_DIR})
set(HAVE_CURL true)

find_package(ZLIB REQUIRED)
include_directories(${ZLIB_INCLUDE_DIR})
set(HAVE_ZLIB true)

# Try to find some GNU/Linux libraries.
if (UNIX)
    find_library(MATH_LIBRARY m)

    if (NOT MATH_LIBRARY)
        message(FATAL_ERROR "Could not find math library.")
    endif ()

    find_package(X11)

    if (X11_FOUND)
        include_directories(${X11_INCLUDE_DIR})
        set(HAVE_X11 true)

        # Try to find X11 XMU.
        find_library(X11_XMU_LIBRARY Xmu /usr/openwin/lib)

        if (X11_XMU_LIBRARY)
            set(HAVE_X11_XMU true)
        else ()
            message(STATUS "Warning: X11 XMU not found, some features may be disabled")
        endif ()
    else ()
        message(STATUS "Warning: X11 not found, some features may be disabled")
    endif ()
endif ()

find_library(CRYPT_LIBRARY crypt)

if (CRYPT_LIBRARY)
    set(HAVE_CRYPT true)
else ()
    message(STATUS "Could not find crypt library, encryption of strings such as passwords will be disabled.")
endif ()

find_library(READLINE_LIBRARY readline)

if (READLINE_LIBRARY)
    set(HAVE_READLINE true)
else ()
    message(STATUS "Could not find readline library, simple interactive console will be compiled instead.")
endif ()

find_library(CHECK_LIBRARY check)

if (CHECK_LIBRARY)
    set(HAVE_CHECK true)
else ()
    message(STATUS "Could not find check library, unit tests will not be compiled.")
endif ()

find_package(OpenSSL REQUIRED)
include_directories(${OPENSSL_INCLUDE_DIR})

# This is very ugly. There is essentially a namespace clash between newer
# MinGW and the Windows port of pthreads, and they both define a timespec
# structure. This would be OK if both checked for its existence, but the
# bigger problem is that the two definitions are *INCOMPATIBLE*. Indeed,
# the pthread.h version uses a 32-bit integer for the seconds timestamp,
# while the MinGW time.h one uses a 64-bit one.
#
# The solution below disables the pthread.h declaration. This means that
# any code working with a timespec assumes the MinGW structure declaration,
# and if there is any code involving pthreads that passes around a
# timespec... tough luck.
#
# Also, we need it here, otherwise the threads check below will not set the
# correct libraries to use.
if (MINGW)
    set(CMAKE_C_FLAGS ${CMAKE_C_FLAGS} -DHAVE_STRUCT_TIMESPEC)
    add_definitions(-DHAVE_STRUCT_TIMESPEC)
endif ()

find_package(Threads REQUIRED)

include(CheckIncludeFiles)
include(CheckFunctionExists)

set(CMAKE_REQUIRED_INCLUDES "math.h")
set(CMAKE_REQUIRED_LIBRARIES "m")

# Check for various include files.
check_include_files(fcntl.h HAVE_FCNTL_H)
check_include_files(unistd.h HAVE_UNISTD_H)
check_include_files(sys/time.h HAVE_SYS_TIME_H)
check_include_files(time.h HAVE_TIME_H)
check_include_files(stddef.h HAVE_STDDEF_H)
check_include_files(dirent.h HAVE_DIRENT_H)
check_include_files(sys/ndir.h HAVE_SYS_NDIR_H)
check_include_files(sys/dir.h HAVE_SYS_DIR_H)
check_include_files(sys/socket.h HAVE_SYS_SOCKET_H)
check_include_files(ndir.h HAVE_NDIR_H)
check_include_files(crypt.h HAVE_CRYPT_H)
check_include_files(arpa/inet.h HAVE_ARPA_INET_H)
check_include_files(valgrind/valgrind.h HAVE_VALGRIND_H)

# Check for various functions.
check_function_exists(strerror HAVE_STRERROR)
check_function_exists(strcasecmp HAVE_STRCASECMP)
check_function_exists(strncasecmp HAVE_STRNCASECMP)
check_function_exists(stricmp HAVE_STRICMP)
check_function_exists(strnicmp HAVE_STRNICMP)
check_function_exists(srandom HAVE_SRANDOM)
check_function_exists(srand48 HAVE_SRAND48)
check_function_exists(srand HAVE_SRAND)
check_function_exists(getdtablesize HAVE_GETDTABLESIZE)
check_function_exists(sysconf HAVE_SYSCONF)
check_function_exists(gettimeofday HAVE_GETTIMEOFDAY)
check_function_exists(tempnam HAVE_TEMPNAM)
check_function_exists(strcasestr HAVE_STRCASESTR)
check_function_exists(strdup HAVE_STRDUP)
check_function_exists(strndup HAVE_STRNDUP)
check_function_exists(strtok_r HAVE_STRTOK_R)
check_function_exists(sigaction HAVE_SIGACTION)
check_function_exists(getline HAVE_GETLINE)
check_function_exists(usleep HAVE_USLEEP)
check_function_exists(strnlen HAVE_STRNLEN)
check_function_exists(mkstemp HAVE_MKSTEMP)
check_function_exists(sincos HAVE_SINCOS)
check_function_exists(pselect HAVE_PSELECT)

if (WIN32)
    check_include_files(wspiapi.h HAVE_WSPIAPI_H)
    check_include_files(ws2tcpip.h HAVE_WS2TCPIP_H)
    if (HAVE_WSPIAPI_H OR HAVE_WS2TCPIP_H)
        set(HAVE_GETADDRINFO TRUE)
    endif (HAVE_WSPIAPI_H OR HAVE_WS2TCPIP_H)
elseif (LINUX)
    check_function_exists(getaddrinfo HAVE_GETADDRINFO)
endif ()

try_compile(HAVE_IPV6 ${CMAKE_CURRENT_BINARY_DIR}/compile_tests ${CMAKE_CURRENT_SOURCE_DIR}/cmake/ipv6test.c)

# Generate the CMake configuration header file.
configure_file(cmake.h.def cmake.h)

# Generate a header file with the Git version used to compile the library.
find_program(GIT_SCM git DOC "Git version control")
mark_as_advanced(GIT_SCM)
find_file(GITDIR NAMES .git PATHS ../ NO_DEFAULT_PATH)
set(GITVERSION_H gitversion.h)

if (GIT_SCM AND GITDIR)
    add_custom_command(OUTPUT ${GITVERSION_H}
        COMMAND ${CMAKE_COMMAND} -E echo "#ifndef GITVERSION_H" > ${GITVERSION_H}
        COMMAND ${CMAKE_COMMAND} -E echo_append "#define GITVERSION " >> ${GITVERSION_H}
        COMMAND ${GIT_SCM} --git-dir "${GITDIR}" log -1 "--pretty=format:%h" >> ${GITVERSION_H}
        COMMAND ${CMAKE_COMMAND} -E echo "" >> ${GITVERSION_H}
        COMMAND ${CMAKE_COMMAND} -E echo_append "#define GITAUTHOR " >> ${GITVERSION_H}
        COMMAND ${GIT_SCM} --git-dir "${GITDIR}" log -1 "--pretty=format:%an" >> ${GITVERSION_H}
        COMMAND ${CMAKE_COMMAND} -E echo "" >> ${GITVERSION_H}
        COMMAND ${CMAKE_COMMAND} -E echo_append "#define GITBRANCH " >> ${GITVERSION_H}
        COMMAND ${GIT_SCM} --git-dir "${GITDIR}" rev-parse --abbrev-ref HEAD >> ${GITVERSION_H}
        COMMAND ${CMAKE_COMMAND} -E echo "#endif" >> ${GITVERSION_H}
        DEPENDS ${GITDIR}/logs/HEAD
        VERBATIM
    )
else ()
    add_custom_command(OUTPUT ${GITVERSION_H}
        COMMAND ${CMAKE_COMMAND} -E echo_append "" > ${GITVERSION_H}
        VERBATIM
    )
endif ()

add_custom_target(git_branch DEPENDS ${GITVERSION_H})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}")

set(TOOLKIT_SOURCES
    binreloc.c
    clioptions.c
    colorspace.c
    console.c
    curl.c
    datetime.c
    logger.c
    math.c
    memory.c
    mempool.c
    packet.c
    path.c
    pbkdf2.c
    porting.c
    process.c
    sha1.c
    shstr.c
    signals.c
    socket.c
    socket_crypto.c
    stringbuffer.c
    string.c
    toolkit.c
    x11.c
    )

add_library(${ATRINIK_TOOLKIT} ${TOOLKIT_SOURCES})

target_link_libraries(${ATRINIK_TOOLKIT} ${CURL_LIBRARIES})
target_link_libraries(${ATRINIK_TOOLKIT} ${CMAKE_THREAD_LIBS_INIT})

if (MINGW)
    target_link_libraries(${ATRINIK_TOOLKIT} wsock32 idn wldap32 ssh2 rtmp winmm
            ws2_32 imagehlp)
endif ()

target_link_libraries(${ATRINIK_TOOLKIT} ${ZLIB_LIBRARIES})

# Link math...
if (MATH_LIBRARY)
    target_link_libraries(${ATRINIK_TOOLKIT} ${MATH_LIBRARY})
endif ()

# Link crypt.
if (CRYPT_LIBRARY)
    target_link_libraries(${ATRINIK_TOOLKIT} ${CRYPT_LIBRARY})
endif ()

# Link readline if available.
if (HAVE_READLINE)
    target_link_libraries(${ATRINIK_TOOLKIT} ${READLINE_LIBRARY})
endif ()

if (HAVE_CHECK)
    target_link_libraries(${ATRINIK_TOOLKIT} ${CHECK_LIBRARY})

    if (UNIX AND NOT APPLE)
        target_link_libraries(${ATRINIK_TOOLKIT} rt)
    endif ()
endif ()

# Link X11 if available.
if (HAVE_X11)
    target_link_libraries(${ATRINIK_TOOLKIT} ${X11_LIBRARIES})
endif ()

# Link X11 XMU if available.
if (HAVE_X11_XMU)
    target_link_libraries(${ATRINIK_TOOLKIT} ${X11_XMU_LIBRARY})
endif ()

target_link_libraries(${ATRINIK_TOOLKIT} ${OPENSSL_LIBRARIES})

add_dependencies(${ATRINIK_TOOLKIT} git_branch)
