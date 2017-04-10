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
    msg
  FILES
    OptionalFields.msg
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


