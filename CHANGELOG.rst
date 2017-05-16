^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package pyros_msgs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Forthcoming
-----------
* Merge pull request `#16 <https://github.com/asmodehn/pyros-msgs/issues/16>`_ from yotabits/nested_implement
  Added test for time in opt_as_nested
* now nesting using type checker method instead of duplicating it.
* Added test for time in opt_as_nested
  The actual test seems to be failing because the type checker seems to be waiting
  for int32 datatype instead of uint32
* Merge pull request `#10 <https://github.com/asmodehn/pyros-msgs/issues/10>`_ from yotabits/nested_implement
  Adding tests in opt_as_nested
* Added test for duration in opt_as_nested
* Added test for std_empty in opt_as_nested
* Added test for string in opt_as_nested
  This include also a small bug fix in the typechecker, now object of type any
  can "contain" objects of type any aswell
* stand alone working
* Fixed test_opt_duration in opt_as_array
  Actually Ros does not allow to have negative nano-seconds:
  1s, -100 000 000ns
  will be transformed into
  900 000 ns
  in the case we test with limit values this could create issues
  so the testing limit values have been changed
* Merge pull request `#3 <https://github.com/asmodehn/pyros-msgs/issues/3>`_ from asmodehn/nested_implement
  Nested implement
* testing...
* testing...
* testing...
* Added test for uint64 in opt_as_nested
* Added test for uint32 in opt_as_nested
* Added test for uint16 in opt_as_nested
* Added test for uint8 in opt_as_nested
* Adapted all int type size tests
* fixing yaml dependency name
* adding quantified code badge
* adding yaml as dependency since our genpy source code relies on it.
* cleaning up doc and comments
* Merge pull request `#2 <https://github.com/asmodehn/pyros-msgs/issues/2>`_ from asmodehn/nested_implement
  Nested implement
* Added test for int64 in opt_as_nested
* Merge pull request `#9 <https://github.com/asmodehn/pyros-msgs/issues/9>`_ from asmodehn/fixing_catkin_tests
  Fixing catkin tests
* fixing array test to use new msg_generate
* Added test for int32 in opt_as_nested
* Added test for int16 in opt_as_nested
* Merge branch 'nested_implement' of https://github.com/asmodehn/pyros-msgs into fixing_catkin_tests
* fixing import_msgsrv to handle namespace packages properly.
  recovered accidently lost comment for namespace package in __init_\_.
* Small fix on test_opt_int8 in opt_as_nested
* fixing setup.py usage of generator
* fixing generator tests
* Added test for int8 in opt_as_nested
* refactored how we do generation to privilege the common usecase.
  now generating message into a temporary directory.
  fixed all tests for basic pytest.
* Merge pull request `#8 <https://github.com/asmodehn/pyros-msgs/issues/8>`_ from yotabits/nested_implement
  Nested implement
* Added test for uint64 in opt_as_array
* Added test for uint32 in opt_as_array
* fixing a bunch of tests for catkin. WIP before rosmsg_generator refactor.
* Added test for uint16 in opt_as_array
* Added test for uint8 in opt_as_array
* Added test for int16 and int 32
  Added test for int16 and int32 for opt_as_array
* fixing pyros_msgs.msg path in nested test
* WIP. attempting to generate all messages at once
  so that starting tests in same or different interpreter doesnt matter anymore
* fixing hardcoded path of generator for test.
* Merge pull request `#1 <https://github.com/asmodehn/pyros-msgs/issues/1>`_ from asmodehn/nested_implement
  Nested implement
* adding importer tests into tox
* fixing path for package message
  adding test for using rosmsg_generator module directly
  fixing tests
* tox fixes...
* improving code to make it more ROS independent.
* improved message generation and tests
* moving ros_genmsg_py and improving API
* fixed all tests
  but still a problem remain : reloading package of newly generated module...
* fixing all tests for opt_as_array with runtime message generation
* fix to handle rosmsg_py dependency path search during generation.
* adapted set_opt_bool to dynamically generate and import message class for tests.
* some fixes still WIP
* making test work for jade. But we still depend on pure ROS package pyros_utils.
* adding pyros-setup as dependency, plus a few comments
* found a method usable by tox to generate ros messages. needs refining...
* adding setup.py custom command to generate message modules.
* fixing test assert that could break on set repr with different order
* modifying travis script to run pytest directly on install directory.
* adding python-pytest dependency
* fixing travis checks
* more common -> typecheck renaming
* fixing setup.py with proper name
* renamed subpackage common to typecheck. fixed tests.
* adding tests and dependency on hypothesis
* adding dependency on hypothesis. now patching messages inside opt_as_array package
* finalizing optional fields as nested implementation
* fixing basic common tests to work with xenial version of hypothesis.
* fixing imports for test runs. other small fixes.
* refining tests
* reorganized tests.
* Merge pull request `#5 <https://github.com/asmodehn/pyros-msgs/issues/5>`_ from asmodehn/hypothesis
  Hypothesis
* adding catkin_pip as dependency
* small improvements. all array tests running...
* fixing array tests
* now seems to work fine with catkin_pip
* fixing opt_as_array tests
* now able to generate type checker from rosmsg type
* improved type checker tests
* more typechecker hypothesis tests
* improved typechecker, not relying on ROS types for it anymore.
* experimenting with hypothesis for proper testing
* opt_as_nested seems to work fine now. more tests required...
* all opt_as_array tests passing
* better type checking by introducing typeschemas
* start of refactor to allow multiple implementations for optional fields... added lots of doctests.
* adding travis badge
* updating Readme to reflect opt_as_nested as WIP
* now travis uses shadow-fixed repository
* adding pyros_utils as dependency
* adding python-six as system dependency
* Merge pull request `#1 <https://github.com/asmodehn/pyros-msgs/issues/1>`_ from asmodehn/http
  optional fields implemented as array
* Merge branch 'http' of https://github.com/asmodehn/pyros-msgs into http
* cleaning up wrong init file
* Merge branch 'master' into http
* adding README
* adding _opt_slots field to the punched message type.
  other changes to get all httpbin tests to pass.
* slightly different way to initializa when doing opt_as_array
* attempting travis fix. comments.
* resurrecting optional message fields, since it is necessary to make explicit the intent of having an optional field in a message.
* added readme for dropping repo.
* WIP. commit before changing internal dict representation of optional messages
* extending path if needed to get ros generated messages. useful when running from here (nose has his own import behavior).
* adding http status code message
* base optional message types and test template
* cleanup bad __init_\_ file. added ignore for *.pyc and build/
* small refactoring. fixed all tests.
* adding dependency on marshmallow
* adding roslint as build depend
* standard message types implemented with doc test. added travis files.
* Started implementing standard ROS message -> dict serialization
* Initial commit
* Contributors: AlexV, Thomas, alexv, yotabits
