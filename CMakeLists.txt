##############################################################################
# CMake
##############################################################################

cmake_minimum_required(VERSION 2.8.3)
project(pyros_msgs)

##############################################################################
# Find Packages
##############################################################################

find_package(catkin REQUIRED COMPONENTS
    roslint
    std_msgs
    message_generation
    message_runtime
)


catkin_python_setup()


# Lint Python modules
file(GLOB_RECURSE ${PROJECT_NAME}_PY_SRCS
     RELATIVE ${PROJECT_SOURCE_DIR} src/pyros_msgs/*.py)
roslint_python(${${PROJECT_NAME}_PY_SRCS})


#####
# MESSAGES
#####

add_message_files(
  DIRECTORY
    msg/opt_as_nested
  FILES
    opt_empty.msg
    opt_bool.msg
    opt_int8.msg
    opt_int16.msg
    opt_int32.msg
    opt_int64.msg
    opt_uint8.msg
    opt_uint16.msg
    opt_uint32.msg
    opt_uint64.msg
    opt_float32.msg
    opt_float64.msg
    opt_string.msg
    opt_time.msg
    opt_duration.msg
    opt_header.msg
)

add_message_files(
  DIRECTORY
    msg/opt_as_array
  FILES
    test_opt_empty_as_array.msg
    test_opt_bool_as_array.msg
    test_opt_int8_as_array.msg
    test_opt_int16_as_array.msg
    test_opt_int32_as_array.msg
    test_opt_int64_as_array.msg
    test_opt_uint8_as_array.msg
    test_opt_uint16_as_array.msg
    test_opt_uint32_as_array.msg
    test_opt_uint64_as_array.msg
    test_opt_float32_as_array.msg
    test_opt_float64_as_array.msg
    test_opt_string_as_array.msg
    test_opt_time_as_array.msg
    test_opt_duration_as_array.msg
    test_opt_header_as_array.msg
)

generate_messages(DEPENDENCIES std_msgs)



##############################################################################
# Catkin
##############################################################################

catkin_package()

#########
# Tests
#######

if (CATKIN_ENABLE_TESTING)
  catkin_add_nosetests(tests)
endif()


