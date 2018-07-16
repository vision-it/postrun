#!/usr/bin/env python3


import pytest
import os
import unittest.mock as mock

import postrun

@pytest.fixture
def module():

    mod = {'roles': {'ref': 'production', 'url': 'https://github.com/vision-it/puppet-roles.git'}}
    return mod

@pytest.mark.deploy
def test_moduledeployer_init(module):
    """
    Test instantiation of ModuleDeployer
    """

    mock_logger = mock.MagicMock()
    directory = os.path.dirname(os.path.realpath(__file__))
    md = postrun.ModuleDeployer(dir_path=directory,
                                is_vagrant=False,
                                logger=mock_logger,
                                modules=module,
                                environment='foobar')

    assert(md.hiera_path == '/etc/puppetlabs/code/hieradata/foobar')

@pytest.mark.deploy
@mock.patch('os.symlink')
def test_moduledeployer_deploy_local(mock_sym,  module):
    """
    Test that the MD makes local symlinks
    """

    mock_logger = mock.MagicMock()
    md = postrun.ModuleDeployer(dir_path='/',
                                is_vagrant=False,
                                logger=mock_logger,
                                modules=module,
                                environment='foobar')

    md.deploy_local('test_mod', '-')

    mock_sym.assert_called_once_with('/opt/puppet/modules/test-mod', '/test_mod')

@pytest.mark.deploy
@mock.patch('os.symlink')
@mock.patch('postrun.rmdir')
def test_moduledeployer_deploy_hiera(mock_rm, mock_sym,  module):
    """
    Test that hiera deploy calls symlink
    """

    mock_logger = mock.MagicMock()
    md = postrun.ModuleDeployer(dir_path='/',
                                is_vagrant=False,
                                logger=mock_logger,
                                modules=module,
                                environment='foobar')

    md.deploy_hiera()

    mock_sym.assert_called_once_with('/opt/puppet/hiera', '/etc/puppetlabs/code/hieradata/foobar')

@pytest.mark.deploy
@mock.patch('os.path.exists', return_value=True)
def test_moduledeployer_has_opt_module(mock_path, module):
    """
    Test correct return value
    """

    mock_logger = mock.MagicMock()
    md = postrun.ModuleDeployer(dir_path='/tmp',
                                is_vagrant=False,
                                logger=mock_logger,
                                modules=module,
                                environment='foobar')

    return_val = md.has_opt_module('my_mod')

    assert((True, '_') == return_val)

@pytest.mark.deploy
@mock.patch('postrun.rmdir')
@mock.patch('postrun.clone_module')
def test_moduledeployer_deploy_modules_regular(mock_clone, mock_rmdir, module):
    """
    Test that git clone gets called
    """

    mock_logger = mock.MagicMock()
    md = postrun.ModuleDeployer(dir_path='/tmp',
                                is_vagrant=False,
                                logger=mock_logger,
                                modules=module,
                                environment='foobar')

    md.deploy_modules()

    mock_rmdir.assert_called_once_with('/tmp/roles')
    mock_clone.assert_called_once_with(('roles',
                                        {'url': 'https://github.com/vision-it/puppet-roles.git',
                                         'ref': 'production'}), '/tmp', mock_logger)


@pytest.mark.deploy
@mock.patch('postrun.rmdir')
@mock.patch('postrun.ModuleDeployer.deploy_hiera')
@mock.patch('postrun.ModuleDeployer.deploy_local')
@mock.patch('postrun.ModuleDeployer.has_opt_module', return_value=(True, '_'))
@mock.patch('postrun.clone_module')
def test_moduledeployer_deploy_modules_vagrant_local(mock_clone, mock_opt, mock_local, mock_hiera, mock_rmdir, module):
    """
    Test that symlinks get set in vagrant
    """

    mock_logger = mock.MagicMock()
    md = postrun.ModuleDeployer(dir_path='/tmp',
                                is_vagrant=True,
                                logger=mock_logger,
                                modules=module,
                                environment='foobar')

    md.deploy_modules()

    mock_rmdir.assert_called_once_with('/tmp/roles')
    mock_local.assert_called_once_with('roles', '_')

@pytest.mark.deploy
@mock.patch('postrun.rmdir')
@mock.patch('postrun.ModuleDeployer.deploy_hiera')
@mock.patch('postrun.ModuleDeployer.deploy_local')
@mock.patch('postrun.ModuleDeployer.has_opt_module', return_value=(False, '_'))
@mock.patch('postrun.clone_module')
def test_moduledeployer_deploy_modules_vagrant_git(mock_clone, mock_opt, mock_local, mock_hiera, mock_rmdir, module):
    """
    Test that git clone gets called  in vagrant
    """

    mock_logger = mock.MagicMock()
    md = postrun.ModuleDeployer(dir_path='/tmp',
                                is_vagrant=True,
                                logger=mock_logger,
                                modules=module,
                                environment='foobar')

    md.deploy_modules()

    mock_rmdir.assert_called_once_with('/tmp/roles')
    mock_clone.assert_called_once_with(('roles',
                                        {'url': 'https://github.com/vision-it/puppet-roles.git',
                                         'ref': 'production'}), '/tmp', mock_logger)
