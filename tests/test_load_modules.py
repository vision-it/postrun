#!/usr/bin/env python3


import pytest
import os
import unittest.mock as mock

import postrun


@pytest.fixture
def module():

    mod = {'roles': {'ref': 'production', 'url': 'https://github.com/vision-it/puppet-roles.git'}}
    return mod


@pytest.mark.modules
def test_load_modules_real_env():
    """
    Test if real location gets loaded
    """

    mock_logger = mock.MagicMock()
    expected_mod = {'other_mod':
                    {'ref': 'master', 'url': 'https://github.com/vision-it/puppet-roles.git'}}

    directory = os.path.dirname(os.path.realpath(__file__))
    loaded_mod = postrun.load_modules(directory,
                                      mock_logger,
                                      environment='',
                                      location='real_loc')

    assert(loaded_mod == expected_mod)


@pytest.mark.modules
def test_load_modules_no_loc(module):
    """
    Test if no location is available in modules.yaml. Should return default location.
    """

    mock_logger = mock.MagicMock()
    directory = os.path.dirname(os.path.realpath(__file__))
    loaded_mod = postrun.load_modules(directory,
                                      mock_logger,
                                      environment='',
                                      location='not_loc')

    assert(loaded_mod == module)


@pytest.mark.modules
def test_load_modules_no_file():
    """
    Test if empty dict is returned if no modules.yaml is available
    """

    mock_logger = mock.MagicMock()
    mod = postrun.load_modules('/foobar', mock_logger, 'staging')

    assert(mod == {})
