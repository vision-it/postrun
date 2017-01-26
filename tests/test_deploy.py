#!/usr/bin/env python3


import pytest
import os
import unittest.mock as mock

import postrun


@pytest.mark.deploy
@mock.patch('subprocess.check_call')
@mock.patch('shutil.rmtree')
def test_deploy_modules(mock_rm, mock_call):
    """
    Test that deploy modules calls git to get a module
    """

    mock_logger = mock.MagicMock()
    directory = os.path.dirname(os.path.realpath(__file__))
    modules = postrun.load_modules(directory,
                                   mock_logger,
                                   environment='',
                                   location='some_loc')

    postrun.deploy_modules('/foobar', modules, mock_logger)

    mock_call.assert_called_once_with(
        ['git', 'clone', '--depth', '1', 'https://github.com/vision-it/puppet-roles.git', '-b', 'master', '/foobar/mod1_name'],
        stderr=-1,
        stdout=-1,
        timeout=30
    )


@pytest.mark.deploy
@mock.patch('postrun.deploy_hiera')
@mock.patch('postrun.clone_module')
@mock.patch('os.symlink')
@mock.patch('postrun.rmdir')
def test_deploy_modules_vagrant_clone(mock_clear, mock_sym, mock_clone, mock_hiera):
    """
    Test that Hiera and Modules (via git) are deployed in Vagrant
    """

    mock_logger = mock.MagicMock()

    directory = os.path.dirname(os.path.realpath(__file__))
    modules = postrun.load_modules(directory, mock_logger, environment='', location='some_loc')

    postrun.deploy_modules_vagrant('/foobar', modules, mock_logger)

    mock_hiera.assert_called_once_with('/etc/puppetlabs/code/hieradata/production')
    assert(mock_clone.call_count == 1)
    assert(mock_sym.call_count == 0)


@pytest.mark.deploy
@mock.patch('postrun.has_opt_module')
@mock.patch('postrun.deploy_hiera')
@mock.patch('postrun.clone_module')
@mock.patch('os.symlink')
@mock.patch('postrun.rmdir')
def test_deploy_modules_vagrant_sym(mock_clear, mock_sym, mock_clone, mock_hiera, mock_hasmod):
    """
    Test that Hiera and Modules (via symlink) are deployed in Vagrant.
    Using underscores
    """

    mock_logger = mock.MagicMock()

    directory = os.path.dirname(os.path.realpath(__file__))
    modules = postrun.load_modules(directory, mock_logger, environment='', location='some_loc')
    mock_hasmod.return_value = (True, '_')

    postrun.deploy_modules_vagrant('/foobar', modules, mock_logger)

    mock_hiera.assert_called_once_with('/etc/puppetlabs/code/hieradata/production')
    mock_sym.assert_called_once_with('/opt/puppet/modules/mod1_name', '/foobar/mod1_name')

    assert(mock_clone.call_count == 0)
    assert(mock_hasmod.call_count == 1)
    assert(mock_clear.call_count == 1)


@pytest.mark.deploy
@mock.patch('postrun.has_opt_module')
@mock.patch('postrun.deploy_hiera')
@mock.patch('postrun.clone_module')
@mock.patch('os.symlink')
@mock.patch('postrun.rmdir')
def test_deploy_modules_vagrant_sym_dash(mock_clear, mock_sym, mock_clone, mock_hiera, mock_hasmod):
    """
    Test that Hiera and Modules (via symlink) are deployed in Vagrant.
    Using dashes.
    """

    mock_logger = mock.MagicMock()
    directory = os.path.dirname(os.path.realpath(__file__))
    modules = postrun.load_modules(directory, mock_logger, environment='', location='some_loc')
    mock_hasmod.return_value = (True, '-')

    postrun.deploy_modules_vagrant('/foobar', modules, mock_logger)

    mock_hiera.assert_called_once_with('/etc/puppetlabs/code/hieradata/production')
    mock_sym.assert_called_once_with('/opt/puppet/modules/mod1-name', '/foobar/mod1_name')

    assert(mock_clone.call_count == 0)
    assert(mock_hasmod.call_count == 1)
