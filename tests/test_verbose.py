#!/usr/bin/env python3


import pytest
import os
import unittest.mock as mock

import postrun


@pytest.fixture(scope='session')
def mock_logger():

    return postrun.create_logger(log_format='[%(levelname)s]: %(message)s',
                                 log_file='/tmp/pytest-postrun.log',
                                 verbose=True)


@pytest.fixture
def module():

    mod = {'roles': {'ref': 'production', 'url': 'https://github.com/vision-it/puppet-roles.git'}}
    return mod


@pytest.mark.verbose
@mock.patch('os.path.isfile', return_value=False)
def test_ModulesLoader_no_modulesyaml(mock_isfile, mock_logger, capfd):
    """
    Test output with no modules.yaml
    """

    ml = postrun.ModuleLoader(dir_path='/tmp',
                              logger=mock_logger,
                              environment='staging',
                              location='some_loc')

    ml.load_modules_file()
    out, err = capfd.readouterr()

    assert(out == '[ERROR]: /tmp/staging/modules.yaml not found for staging\n')

@pytest.mark.verbose
@mock.patch('os.path.isfile', return_value=False)
def test_ModulesLoader_using_default(mock_isfile, mock_logger, capfd):
    """
    Test output with default location
    """

    ml = postrun.ModuleLoader(dir_path='/tmp',
                              logger=mock_logger,
                              environment='staging',
                              location='some_loc')

    ml.load_modules_file = mock.MagicMock()
    ml.load_modules_file.return_value = {}

    ml.load_modules_from_yaml()
    out, err = capfd.readouterr()

    assert(out == '[INFO]: configuration for location some_loc not found, using default\n')


@pytest.mark.verbose
def test_ModulesLoader_no_module(mock_logger, capfd):
    """
    Test outwith with nonexisting module
    """

    directory = os.path.dirname(os.path.realpath(__file__))
    ml = postrun.ModuleLoader(dir_path=directory,
                              logger=mock_logger,
                              environment='',
                              module='foobar',
                              branch='new_branch',
                              location='default')

    ml.get_modules()
    out, err = capfd.readouterr()

    assert(out == '[ERROR]: Module foobar not found in configuration\n')


@pytest.mark.xfail
@pytest.mark.verbose
@mock.patch('postrun.git')
def test_clone_module_fail_verbose(mock_git, mock_logger, capfd):
    """
    Test output with git error
    """

    mock_git.side_effect = RuntimeError('foo')
    module = ('roles',
              {'url': 'https://github.com/vision-it/foobar.git', 'ref': 'notabranch'})

    postrun.clone_module(module=module, target_directory='/tmp', logger=mock_logger)
    out, err = capfd.readouterr()

    assert(out == '[ERROR]: Error while cloning roles\n')
