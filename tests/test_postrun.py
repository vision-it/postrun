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


@pytest.mark.util
@mock.patch('shutil.rmtree')
@mock.patch('os.makedirs')
def test_clear_folder(mock_mkdir, mock_rm):

    postrun.clear_folder('/puppet/foobar')
    mock_rm.assert_called_once_with('/puppet/foobar')
    mock_mkdir.assert_called_once_with('/puppet/foobar')


@pytest.mark.util
def test_load_yaml(module):

    directory = os.path.dirname(os.path.realpath(__file__))
    testfile = os.path.join(directory, "modules.yaml")
    loaded_mod = postrun.load_yaml(testfile)

    assert(module == loaded_mod['modules']['default'])


@pytest.mark.git
@mock.patch('subprocess.check_call')
def test_clone_module_fail(mock_call, mock_logger, capfd):

    mock_call.side_effect = KeyError('foo')
    module = ('roles',
              {'url': 'https://github.com/vision-it/foobar.git', 'ref': 'notabranch'})

    postrun.clone_module(module, '/tmp', mock_logger)
    out, err = capfd.readouterr()

    assert(out == '[ERROR]: Error while cloning roles\n')


@pytest.mark.util
def test_has_opt_module_false():

    return_val = postrun.has_opt_module('foobar')
    assert(return_val == (False, '-'))


@pytest.mark.util
@mock.patch('os.path.exists')
def test_has_opt_module_true(mock_os):

    mock_os.return_value = True

    return_val = postrun.has_opt_module('/opt', 'foobar')
    assert(return_val == (True, '_'))


@pytest.mark.hiera
@mock.patch('os.symlink')
@mock.patch('os.remove')
@mock.patch('shutil.rmtree')
def test_deploy_hiera_with_folder(mock_rmtree, mock_remove, mock_sym):

    postrun.deploy_hiera(hiera_dir='/hiera/foobar/folder')

    mock_rmtree.assert_called_once_with('/hiera/foobar/folder')
    assert(mock_remove.call_count == 0)

    mock_sym.assert_called_once_with('/opt/puppet/hiera', '/hiera/foobar/folder')


@pytest.mark.hiera
@mock.patch('os.path.islink')
@mock.patch('os.symlink')
@mock.patch('os.remove')
@mock.patch('shutil.rmtree')
def test_deploy_hiera_with_sym(mock_rmtree, mock_remove, mock_sym, mock_islink):

    mock_islink.return_value = True
    postrun.deploy_hiera(hiera_dir='/hiera/foobar/symlink')

    mock_remove.assert_called_once_with('/hiera/foobar/symlink')
    assert(mock_rmtree.call_count == 0)

    mock_sym.assert_called_once_with('/opt/puppet/hiera', '/hiera/foobar/symlink')


@pytest.mark.git
@mock.patch('subprocess.check_call')
def test_clone_module(mock_call):

    mock_logger = mock.MagicMock()

    module = ('roles',
              {'url': 'https://github.com/vision-it/puppet-roles.git', 'ref': 'production'})

    process_mock = mock.Mock()
    attrs = {'return_value': (b'output', b'error')}
    process_mock.configure_mock(**attrs)
    mock_call.return_value = process_mock

    postrun.clone_module(module, '/foobar', mock_logger)

    mock_call.assert_called_once_with(['git',
                                       'clone',
                                       'https://github.com/vision-it/puppet-roles.git',
                                       '-b',
                                       'production',
                                       '/foobar/roles'],
                                      stderr=-1,
                                      stdout=-1,
                                      timeout=20)


@pytest.mark.util
def test_is_vagrant():

    virtual = postrun.is_vagrant()
    assert(virtual == False)


@pytest.mark.util
@mock.patch('subprocess.Popen')
def test_get_location_exception(mock_popen):

    mock_popen.side_effect = KeyError('foo')

    location = postrun.get_location()

    mock_popen.assert_called_once_with('facter location',
                                       close_fds=True,
                                       shell=True,
                                       stderr=-2,
                                       stdin=-1,
                                       stdout=-1)

    assert(location == 'default')


@pytest.mark.util
@mock.patch('subprocess.Popen')
def test_get_location(mock_popen):

    process_mock = mock.Mock()
    attrs = {'communicate.return_value': (b'output', b'error')}
    process_mock.configure_mock(**attrs)
    mock_popen.return_value = process_mock

    location = postrun.get_location()

    mock_popen.assert_called_once_with('facter location',
                                       close_fds=True,
                                       shell=True,
                                       stderr=-2,
                                       stdin=-1,
                                       stdout=-1)

    assert(location == 'output')


@pytest.mark.modules
def test_load_modules_real_env():

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
def test_load_modules_no_loc(module, mock_logger, capfd):

    directory = os.path.dirname(os.path.realpath(__file__))
    loaded_mod = postrun.load_modules(directory,
                                      mock_logger,
                                      environment='',
                                      location='not_loc')

    out, err = capfd.readouterr()

    assert(loaded_mod == module)
    assert (out == '[WARNING]: No module configuration for not_loc, use default\n')


@pytest.mark.modules
def test_load_modules_no_file(mock_logger, capfd):

    mod = postrun.load_modules('/foobar', mock_logger, 'staging')
    out, err = capfd.readouterr()

    assert(mod == {})
    assert (out == '[ERROR]: No modules.yaml found for staging\n')


@pytest.mark.deploy
@mock.patch('subprocess.check_call')
def test_deploy_modules(mock_call):

    mock_logger = mock.MagicMock()
    directory = os.path.dirname(os.path.realpath(__file__))
    modules = postrun.load_modules(directory,
                                   mock_logger,
                                   environment='',
                                   location='some_loc')

    postrun.deploy_modules('/foobar', modules, mock_logger)

    mock_call.assert_called_once_with(
        ['git', 'clone', 'https://github.com/vision-it/puppet-roles.git', '-b', 'master', '/foobar/mod1_name'],
        stderr=-1,
        stdout=-1,
        timeout=20
    )


@pytest.mark.deploy
@mock.patch('subprocess.check_call')
def test_deploy_modules_verbose(mock_call, mock_logger, capfd):

    directory = os.path.dirname(os.path.realpath(__file__))
    modules = postrun.load_modules(directory,
                                   mock_logger,
                                   environment='',
                                   location='some_loc')

    postrun.deploy_modules('/foobar', modules, mock_logger)
    out, err = capfd.readouterr()

    assert (out == '[DEBUG]: Deploying git mod1_name\n')


@pytest.mark.deploy
@mock.patch('postrun.deploy_hiera')
@mock.patch('postrun.clone_module')
@mock.patch('os.symlink')
def test_deploy_modules_vagrant_verbose(mock_sym, mock_clone, mock_hiera, mock_logger, capfd):

    directory = os.path.dirname(os.path.realpath(__file__))
    modules = postrun.load_modules(directory, mock_logger,  environment='', location='some_loc')

    postrun.deploy_modules_vagrant('/foobar', modules, mock_logger)
    out, err = capfd.readouterr()

    assert (out == "[DEBUG]: Deploying git mod1_name\n")


@pytest.mark.deploy
@mock.patch('postrun.deploy_hiera')
@mock.patch('postrun.clone_module')
@mock.patch('os.symlink')
def test_deploy_modules_vagrant_clone(mock_sym, mock_clone, mock_hiera):

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
def test_deploy_modules_vagrant_sym(mock_sym, mock_clone, mock_hiera, mock_hasmod):

    mock_logger = mock.MagicMock()

    directory = os.path.dirname(os.path.realpath(__file__))
    modules = postrun.load_modules(directory, mock_logger, environment='', location='some_loc')
    mock_hasmod.return_value = (True, '_')

    postrun.deploy_modules_vagrant('/foobar', modules, mock_logger)

    mock_hiera.assert_called_once_with('/etc/puppetlabs/code/hieradata/production')
    mock_sym.assert_called_once_with('/opt/puppet/modules/mod1_name', '/foobar/mod1_name')

    assert(mock_clone.call_count == 0)
    assert(mock_hasmod.call_count == 1)


@pytest.mark.deploy
@mock.patch('postrun.has_opt_module')
@mock.patch('postrun.deploy_hiera')
@mock.patch('postrun.clone_module')
@mock.patch('os.symlink')
def test_deploy_modules_vagrant_sym_verbose(mock_sym, mock_clone, mock_hiera, mock_hasmod, mock_logger, capfd):

    directory = os.path.dirname(os.path.realpath(__file__))
    modules = postrun.load_modules(directory, mock_logger, environment='', location='some_loc')
    mock_hasmod.return_value = (True, '_')

    postrun.deploy_modules_vagrant('/foobar', modules, mock_logger)
    out, err = capfd.readouterr()

    assert (out == "[DEBUG]: Deploying local mod1_name\n")


@pytest.mark.deploy
@mock.patch('postrun.has_opt_module')
@mock.patch('postrun.deploy_hiera')
@mock.patch('postrun.clone_module')
@mock.patch('os.symlink')
def test_deploy_modules_vagrant_sym_dash(mock_sym, mock_clone, mock_hiera, mock_hasmod):

    mock_logger = mock.MagicMock()
    directory = os.path.dirname(os.path.realpath(__file__))
    modules = postrun.load_modules(directory, mock_logger, environment='', location='some_loc')
    mock_hasmod.return_value = (True, '-')

    postrun.deploy_modules_vagrant('/foobar', modules, mock_logger)

    mock_hiera.assert_called_once_with('/etc/puppetlabs/code/hieradata/production')
    mock_sym.assert_called_once_with('/opt/puppet/modules/mod1-name', '/foobar/mod1_name')

    assert(mock_clone.call_count == 0)
    assert(mock_hasmod.call_count == 1)


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
    assert(mock_clear.call_count == 2)
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
    assert(mock_clear.call_count == 2)
    assert(mock_deploy.call_count == 2)
    assert(mock_mods.call_count == 2)
    assert(mock_log.call_count == 1)


@pytest.mark.main
@mock.patch('argparse.ArgumentParser')
def test_commandline(mock_parser):

    postrun.commandline()
    assert(mock_parser.call_count == 1)
