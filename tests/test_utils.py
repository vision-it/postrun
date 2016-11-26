#!/usr/bin/env python3


import pytest
import os
import unittest.mock as mock

import postrun


@pytest.fixture
def module():

    mod = {'roles': {'ref': 'production', 'url': 'https://github.com/vision-it/puppet-roles.git'}}
    return mod


@pytest.mark.utils
@mock.patch('shutil.rmtree')
@mock.patch('os.makedirs')
def test_clear_folder(mock_mkdir, mock_rm):

    postrun.clear_folder('/puppet/foobar')
    mock_rm.assert_called_once_with('/puppet/foobar')
    mock_mkdir.assert_called_once_with('/puppet/foobar')


@pytest.mark.utils
def test_load_yaml(module):

    directory = os.path.dirname(os.path.realpath(__file__))
    testfile = os.path.join(directory, "modules.yaml")
    loaded_mod = postrun.load_yaml(testfile)

    assert(module == loaded_mod['modules']['default'])


@pytest.mark.utils
def test_has_opt_module_false():

    return_val = postrun.has_opt_module('foobar')
    assert(return_val == (False, '-'))


@pytest.mark.utils
@mock.patch('os.path.exists')
def test_has_opt_module_true(mock_os):

    mock_os.return_value = True

    return_val = postrun.has_opt_module('/opt', 'foobar')
    assert(return_val == (True, '_'))


@pytest.mark.utils
@mock.patch('os.symlink')
@mock.patch('os.remove')
@mock.patch('shutil.rmtree')
def test_deploy_hiera_with_folder(mock_rmtree, mock_remove, mock_sym):

    postrun.deploy_hiera(hiera_dir='/hiera/foobar/folder')

    mock_rmtree.assert_called_once_with('/hiera/foobar/folder')
    mock_sym.assert_called_once_with('/opt/puppet/hiera', '/hiera/foobar/folder')
    assert(mock_remove.call_count == 0)


@pytest.mark.utils
@mock.patch('os.path.islink')
@mock.patch('os.symlink')
@mock.patch('os.remove')
@mock.patch('shutil.rmtree')
def test_deploy_hiera_with_sym(mock_rmtree, mock_remove, mock_sym, mock_islink):

    mock_islink.return_value = True
    postrun.deploy_hiera(hiera_dir='/hiera/foobar/symlink')

    mock_remove.assert_called_once_with('/hiera/foobar/symlink')
    mock_sym.assert_called_once_with('/opt/puppet/hiera', '/hiera/foobar/symlink')
    assert(mock_rmtree.call_count == 0)


@pytest.mark.utils
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


@pytest.mark.utils
def test_is_vagrant():

    virtual = postrun.is_vagrant()

    assert(virtual == False)


@pytest.mark.utils
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


@pytest.mark.utils
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
