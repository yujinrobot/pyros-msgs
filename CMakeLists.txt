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

add_message_files(
  DIRECTORY
    msg
  FILES
    HttpRequest.msg
    HttpResponse.msg
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


