#!/usr/bin/env python3


import pytest
import os
import unittest.mock as mock

import postrun


@pytest.fixture(scope='session')
def mock_logger():

    return postrun.Logger(log_format='[%(levelname)s]: %(message)s',
                          log_file='/tmp/pytest-postrun.log',
                          verbose=True)


@pytest.fixture
def module():

    mod = {'roles': {'ref': 'production', 'url': 'https://github.com/vision-it/puppet-roles.git'}}
    return mod


@pytest.mark.verbose
def test_load_modules_not_mod_verbose(mock_logger, capfd):

    directory = os.path.dirname(os.path.realpath(__file__))
    mod = postrun.load_modules(directory,
                               mock_logger,
                               environment='',
                               location='some_loc',
                               module_to_load='im_not_a_module')

    out, err = capfd.readouterr()

    assert(out == '[ERROR]: im_not_a_module not found in modules.yaml\n')


@pytest.mark.verbose
def test_load_modules_no_loc_verbose(module, mock_logger, capfd):

    directory = os.path.dirname(os.path.realpath(__file__))
    loaded_mod = postrun.load_modules(directory,
                                      mock_logger,
                                      environment='',
                                      location='not_loc')

    out, err = capfd.readouterr()

    assert(out == '[WARNING]: No module configuration for not_loc, use default\n')


@pytest.mark.verbose
@mock.patch('postrun.rmdir')
def test_load_modules_no_file_verbose(mock,mock_logger, capfd):

    mod = postrun.load_modules('/foobar', mock_logger, 'staging')
    out, err = capfd.readouterr()

    assert(out == '[ERROR]: No modules.yaml found for staging\n')


@pytest.mark.verbose
@mock.patch('subprocess.check_call')
@mock.patch('shutil.rmtree')
def test_deploy_modules_verbose(mock_rm, mock_call, mock_logger, capfd):

    directory = os.path.dirname(os.path.realpath(__file__))
    modules = postrun.load_modules(directory,
                                   mock_logger,
                                   environment='',
                                   location='some_loc')

    postrun.deploy_modules('/foobar', modules, mock_logger)
    out, err = capfd.readouterr()

    assert (out == '[DEBUG]: Deploying git mod1_name with branch master\n')


@pytest.mark.verbose
@mock.patch('postrun.deploy_hiera')
@mock.patch('postrun.clone_module')
@mock.patch('os.symlink')
@mock.patch('postrun.rmdir')
def test_deploy_modules_vagrant_verbose(mock_clear, mock_sym, mock_clone, mock_hiera, mock_logger, capfd):

    directory = os.path.dirname(os.path.realpath(__file__))
    modules = postrun.load_modules(directory, mock_logger,  environment='', location='some_loc')

    postrun.deploy_modules_vagrant('/foobar', modules, mock_logger)
    out, err = capfd.readouterr()

    assert (out == "[DEBUG]: Deploying git mod1_name with branch master\n")


@pytest.mark.verbose
@mock.patch('postrun.has_opt_module')
@mock.patch('postrun.deploy_hiera')
@mock.patch('postrun.clone_module')
@mock.patch('os.symlink')
@mock.patch('postrun.rmdir')
def test_deploy_modules_vagrant_sym_verbose(mock_clear, mock_sym, mock_clone, mock_hiera, mock_hasmod, mock_logger, capfd):

    directory = os.path.dirname(os.path.realpath(__file__))
    modules = postrun.load_modules(directory, mock_logger, environment='', location='some_loc')
    mock_hasmod.return_value = (True, '_')

    postrun.deploy_modules_vagrant('/foobar', modules, mock_logger)
    out, err = capfd.readouterr()

    assert (out == "[DEBUG]: Deploying local mod1_name\n")


@pytest.mark.verbose
@mock.patch('postrun.git')
def test_clone_module_fail_verbose(mock_git, mock_logger, capfd):

    mock_git.side_effect = RuntimeError('foo')
    module = ('roles',
              {'url': 'https://github.com/vision-it/foobar.git', 'ref': 'notabranch'})

    postrun.clone_module(module=module, target_directory='/tmp', logger=mock_logger)
    out, err = capfd.readouterr()

    assert(out == '[ERROR]: Error while cloning roles\n')
