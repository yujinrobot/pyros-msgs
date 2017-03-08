

# The main point here is insuring that any sanitized type will safely echo over a ROS message



def test_typeschema_(sanitized):
    """
    Verify that sanitized default is of sanitize instance
    :param sanitized:
    :param val:
    :return:
    """
    ts = TypeSchema(sanitized, sanitized)
    assert isinstance(ts.default(), sanitized)

# The other main point here is insuring that any type that doesnt safely echo over ROS will not pass typeschema check