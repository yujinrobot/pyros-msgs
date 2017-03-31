##############################################################################
# CMake
##############################################################################

cmake_minimum_required(VERSION 2.8.3)
project(pyros_msgs)

##############################################################################
# Find Packages
##############################################################################

find_package(catkin REQUIRED COMPONENTS
    catkin_pip
    std_msgs
    message_generation
    message_runtime
)


#####
# MESSAGES
#####

add_message_files(
  DIRECTORY
    msg/opt_as_nested
  FILES
    OptionalFields.msg

    # For testing only
    test_opt_bool_as_nested.msg
)

add_message_files(
  DIRECTORY
    msg/opt_as_array
  FILES

    # For testing only
    test_opt_std_empty_as_array.msg
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

catkin_pip_package(pyros_msgs)

#########
# Tests
#######

if (CATKIN_ENABLE_TESTING)
  catkin_add_pytests(pyros_msgs/typecheck/tests)
  catkin_add_pytests(pyros_msgs/opt_as_array/tests)
  catkin_add_pytests(pyros_msgs/opt_as_nested/tests)
endif()


