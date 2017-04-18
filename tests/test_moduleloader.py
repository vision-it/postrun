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
def test_moduleload_with_real_location():
    """
    Test if real location gets loaded
    """

    mock_logger = mock.MagicMock()
    expected_mod = {'other_mod':
                    {'ref': 'master', 'url': 'https://github.com/vision-it/puppet-roles.git'}}

    directory = os.path.dirname(os.path.realpath(__file__))
    ml = postrun.ModuleLoader(dir_path=directory,
                              logger=mock_logger,
                              environment='',
                              location='real_loc')


    loaded_mod = ml.get_modules()

    assert(loaded_mod == expected_mod)

@pytest.mark.modules
def test_moduleload_with_foobar_location(module):
    """
    Test if default location gets loaded
    """

    mock_logger = mock.MagicMock()
    expected_mod = module

    directory = os.path.dirname(os.path.realpath(__file__))
    ml = postrun.ModuleLoader(dir_path=directory,
                              logger=mock_logger,
                              environment='',
                              location='foobar_loc')


    loaded_mod = ml.get_modules()

    assert(loaded_mod == expected_mod)


@pytest.mark.modules
def test_moduleload_with_branch():
    """
    Test if branch gets updated
    """

    mock_logger = mock.MagicMock()

    expected_mod = {'roles': {'ref': 'new_branch', 'url': 'https://github.com/vision-it/puppet-roles.git'}}


    directory = os.path.dirname(os.path.realpath(__file__))
    ml = postrun.ModuleLoader(dir_path=directory,
                              logger=mock_logger,
                              environment='',
                              module='roles',
                              branch='new_branch',
                              location='default')

    loaded_mod = ml.get_modules()

    assert(loaded_mod == expected_mod)


def test_moduleloader_no_file():
    """
    Test if empty dict is returned if no modules.yaml is available
    """

    mock_logger = mock.MagicMock()
    ml = postrun.ModuleLoader(dir_path='/foobar',
                              logger=mock_logger)


    loaded_mod = ml.get_modules()

    assert(loaded_mod == {})
