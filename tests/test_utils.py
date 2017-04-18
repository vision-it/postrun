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
@mock.patch('os.makedirs')
def test_mkdir_directory(mock_make):
    """
    Test if mkdir creates the directory
    """

    postrun.mkdir('/puppet/foobar/bar')

    mock_make.assert_called_once_with('/puppet/foobar/bar', exist_ok=True)


@pytest.mark.utils
@mock.patch('shutil.rmtree')
@mock.patch('os.remove')
@mock.patch('os.path.exists', return_value=True)
def test_rmdir(mock_path, mock_rm, mock_rmtree,  module):
    """
    Test that rmdir removes a directory
    """

    postrun.rmdir('/tmp/postrun')

    mock_path.assert_called_once_with('/tmp/postrun')
    mock_rmtree.assert_called_once_with('/tmp/postrun')


@pytest.mark.utils
@mock.patch('shutil.rmtree')
@mock.patch('os.remove')
@mock.patch('os.path.exists', return_value=True)
@mock.patch('os.path.islink', return_value=True)
def test_rmdir_link(mock_islink, mock_path, mock_rm, mock_rmtree,  module):
    """
    Test that rmdir removes a symlink
    """

    postrun.rmdir('/tmp/postrun')

    mock_path.assert_called_once_with('/tmp/postrun')
    mock_islink.assert_called_once_with('/tmp/postrun')
    mock_rm.assert_called_once_with('/tmp/postrun')


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
