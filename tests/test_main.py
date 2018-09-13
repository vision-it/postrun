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
@mock.patch('postrun.ModuleLoader')
@mock.patch('postrun.ModuleDeployer')
@mock.patch('postrun.create_logger')
def test_main_no_folder(mock_log, mock_deploy, mock_mods, mock_os, capsys):
    """
    Test main function without existing folder. Should exit with 2
    """

    mock_args = mock.MagicMock()
    mock_os.side_effect = FileNotFoundError()

    with pytest.raises(SystemExit):
        postrun.main(args=mock_args, is_vagrant=False)


@pytest.mark.main
@mock.patch('os.listdir')
@mock.patch('postrun.ModuleLoader')
@mock.patch('postrun.ModuleDeployer')
@mock.patch('postrun.create_logger')
@mock.patch('sys.exit')
@mock.patch('postrun.mkdir')
def test_main_regular(mock_mk, sys_exit, mock_log, mock_deploy, mock_mods, mock_os, module):
    """
    Test main function regularly. Should call deploy_modules
    """

    mock_os.return_value = ['production', 'staging']
    mock_args = mock.MagicMock()

    postrun.main(args=mock_args, is_vagrant=False)

    mock_os.assert_called_once_with('/etc/puppetlabs/code/environments/')
    assert(mock_deploy.call_count == 2)
    assert(mock_mods.call_count == 2)
    assert(mock_log.call_count == 1)
    assert(mock_mk.call_count == 4) # Twice for each environment


@pytest.mark.main
@mock.patch('os.listdir')
@mock.patch('postrun.ModuleLoader')
@mock.patch('postrun.ModuleDeployer')
@mock.patch('postrun.create_logger')
@mock.patch('sys.exit')
@mock.patch('postrun.mkdir')
def test_main_vagrant(mock_mk, sys_exit, mock_log, mock_deploy, mock_mods, mock_os, module):
    """
    Test main function called in Vagrant. Should call deploy_modules_vagrant
    """

    mock_os.return_value = ['production', 'staging']
    mock_args = mock.MagicMock()

    postrun.main(args=mock_args, is_vagrant=True)

    mock_os.assert_called_once_with('/etc/puppetlabs/code/environments/')
    assert(mock_deploy.call_count == 2)
    assert(mock_mods.call_count == 2)
    assert(mock_log.call_count == 1)
    assert(mock_mk.call_count == 4) # Twice for each environment


@pytest.mark.main
def test_commandline_verbosity():
    """
    Test that the verbosity is turned on, and default module return value is all
    """

    test_parser = postrun.commandline(['-v'])

    assert(test_parser.verbose == True)
    assert(test_parser.module == None)

@pytest.mark.main
def test_commandline_module():
    """
    Test that the module commandline arg can be set.
    """

    test_parser = postrun.commandline(['-m', 'foobar'])

    assert(test_parser.module == 'foobar')

@pytest.mark.main
def test_commandline_module():
    """
    Test that the branch commandline arg can be set.
    """

    test_parser = postrun.commandline(['-b', 'foobar'])

    assert(test_parser.branch == 'foobar')
