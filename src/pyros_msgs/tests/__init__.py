# TODO : running all doctest (from pytest)


if __name__ == '__main__':
    import pytest
    pytest.main([
        'type_validation.py',
        '--doctest-modules'
    ])
