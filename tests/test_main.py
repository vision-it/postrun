#!/usr/bin/env python3


import pytest
import os
import unittest.mock as mock

import postrun


@pytest.fixture
def module():

    mod = {'roles': {'ref': 'production', 'url': 'https://github.com/vision-it/puppet-roles.git'}}
    return mod


@pytest.mark.main
@mock.patch('os.listdir')
@mock.patch('postrun.load_modules')
@mock.patch('postrun.clear_folder')
@mock.patch('postrun.deploy_modules')
@mock.patch('postrun.Logger')
def test_main_regular(mock_log, mock_deploy, mock_clear, mock_mods, mock_os, module):

    mock_mods.return_value = module
    mock_os.return_value = ['production', 'staging']
    mock_args = mock.MagicMock()

    postrun.main(args=mock_args, is_vagrant=False)

    mock_os.assert_called_once_with('/etc/puppetlabs/code/environments/')
    assert(mock_deploy.call_count == 2)
    assert(mock_mods.call_count == 2)
    assert(mock_log.call_count == 1)


@pytest.mark.main
@mock.patch('os.listdir')
@mock.patch('postrun.load_modules')
@mock.patch('postrun.clear_folder')
@mock.patch('postrun.deploy_modules_vagrant')
@mock.patch('postrun.Logger')
def test_main_vagrant(mock_log, mock_deploy, mock_clear, mock_mods, mock_os, module):

    mock_mods.return_value = module
    mock_os.return_value = ['production', 'staging']
    mock_args = mock.MagicMock()

    postrun.main(args=mock_args, is_vagrant=True)

    mock_os.assert_called_once_with('/etc/puppetlabs/code/environments/')
    assert(mock_deploy.call_count == 2)
    assert(mock_mods.call_count == 2)
    assert(mock_log.call_count == 1)


@pytest.mark.main
def test_commandline():

    test_parser = postrun.commandline(['-v'])

    assert(test_parser.verbose == True)
