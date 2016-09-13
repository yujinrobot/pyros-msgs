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
     RELATIVE ${PROJECT_SOURCE_DIR} src/pyros_test/*.py)
roslint_python(${${PROJECT_NAME}_PY_SRCS})


#####
# MESSAGES
#####

# add_message_files(
#   DIRECTORY
#     msg/http
#   FILES
#     HttpRequest.msg
#     HttpResponse.msg
# )

add_message_files(
  DIRECTORY
    msg/opt
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

#####
# SERVICES
#####

# add_service_files(
#   DIRECTORY
#     srv
#   FILES
#    httpbin_ip.srv
#    httpbin_get.srv
#    httpbin_post.srv
# )

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


