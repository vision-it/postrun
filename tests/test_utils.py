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
@mock.patch('os.path.exists', return_value=False)
@mock.patch('os.makedirs')
def test_mkdir_directory(mock_exists, mock_make):
    """
    Test if mkdir creates the directory
    """

    postrun.mkdir('/puppet/foobar/bar')

    mock_make.assert_called_once_with('/puppet/foobar/bar')


@pytest.mark.utils
@mock.patch('shutil.rmtree')
@mock.patch('os.remove')
@mock.patch('os.path.exists', return_value=True)
def test_rmdir_directory(mock_exists, mock_remove, mock_rm):
    """
    Test if rmdir removes a real directory
    """

    postrun.rmdir('/puppet/foobar')

    mock_rm.assert_called_once_with('/puppet/foobar')


@pytest.mark.utils
@mock.patch('shutil.rmtree')
@mock.patch('os.remove')
@mock.patch('os.path.exists', return_value=True)
@mock.patch('os.path.islink', return_value=True)
def test_rmdir_symlink(mock_link, mock_exists, mock_remove, mock_rm):
    """
    Test if rmdir removes a symlink
    """

    postrun.rmdir('/puppet/foobar')

    mock_remove.assert_called_once_with('/puppet/foobar')


@pytest.mark.utils
def test_load_yaml(module):
    """
    Test that a yaml file gets loaded.
    """

    directory = os.path.dirname(os.path.realpath(__file__))
    testfile = os.path.join(directory, "modules.yaml")
    loaded_mod = postrun.load_yaml(testfile)

    assert(module == loaded_mod['modules']['default'])


@pytest.mark.utils
def test_has_opt_module_false():
    """
    Test that has_opt_module returns a default value if no /opt folder exists
    """

    return_val = postrun.has_opt_module('foobar')
    assert(return_val == (False, '-'))


@pytest.mark.utils
@mock.patch('os.path.exists', return_value=True)
def test_has_opt_module_true(mock_os):
    """
    Test that has_opt_module return True if /opt folder exists
    """

    return_val = postrun.has_opt_module('/opt', 'foobar')
    assert(return_val == (True, '_'))


@pytest.mark.utils
@mock.patch('os.symlink')
@mock.patch('postrun.rmdir')
def test_deploy_hiera_with_folder(mock_rmdir, mock_sym):
    """
    Test that deploy_hiera (Vagrant) sets the symlink and removes the old folder
    """

    postrun.deploy_hiera(hiera_dir='/hiera/foobar/folder')

    mock_rmdir.assert_called_once_with('/hiera/foobar/folder')
    mock_sym.assert_called_once_with('/opt/puppet/hiera', '/hiera/foobar/folder')


@pytest.mark.utils
@mock.patch('subprocess.check_call')
def test_clone_module(mock_call):
    """
    Test that clone_module calls git
    """

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
                                       '--depth',
                                       '1',
                                       'https://github.com/vision-it/puppet-roles.git',
                                       '-b',
                                       'production',
                                       '/foobar/roles'],
                                      stderr=-1,
                                      stdout=-1,
                                      timeout=30)


@pytest.mark.utils
def test_is_vagrant():
    """
    Test return value of is_vagrant if no /vagrant exists
    """

    virtual = postrun.is_vagrant()

    assert(virtual == False)


@mock.patch('os.path.exists', return_value=True)
@pytest.mark.utils
def test_is_vagrant_true(mock_path):
    """
    Test return value of is_vagrant if /vagrant exists
    """

    virtual = postrun.is_vagrant()

    assert(virtual == True)


@pytest.mark.utils
@mock.patch('subprocess.check_output')
def test_get_location_exception(mock_popen):
    """
    Test return if facter isn't available
    """

    mock_popen.side_effect = KeyError('foo')

    location = postrun.get_location()

    assert(location == 'default')


@pytest.mark.utils
@mock.patch('subprocess.check_output', return_value=b'output')
def test_get_location(mock_popen):
    """
    Test return if facter is available
    """

    location = postrun.get_location()

    mock_popen.assert_called_once_with(['/opt/puppetlabs/bin/facter', 'location'])

    assert(location == 'output')
