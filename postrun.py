#!/usr/bin/env python3


import yaml
import subprocess
import os
import shutil
import sys


# TODO Make git clone multithreaded


def git(*args):
    """
    Subprocess wrapper for git
    """

    return subprocess.check_call(['git'] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def clone_module(module, target_directory):
    """
    Clones a git repository.
    Used to get each module.
    """

    name, values = module
    url = values['url']
    ref = values['ref']
    target = os.path.join(target_directory, name)

    # TODO Catch errors and whatnot
    git('clone', url, '-b', ref, target)


def load_yaml(file_name):
    """
    Loads a YAML file.
    Used to load the modules.yaml
    """

    with open(file_name, 'r') as yaml_file:
        parsed_yaml = yaml.load(yaml_file)

    return parsed_yaml


def clear_folder(dir_path):
    """
    Clears out a directory by removing and recreating it.
    Used to clear out the /dist directory
    """

    shutil.rmtree(dir_path)
    os.makedirs(dir_path)


def is_vagrant():
    """
    Checks if the current machine runs vagrant
    """

    return os.path.exists('/vagrant')


def has_opt_module(module_name, opt_path='/opt/puppet/modules/'):
    """
    Checks if there is there is a module in /opt
    """

    module_path = os.path.join(opt_path, module_name)

    return os.path.exists(module_path)


def get_location():
    """
    Gets the current location fact for this machine.
    Returns default if nothing is found.
    """

    try:
        cmd = 'facter location'
        p = subprocess.Popen(cmd,
                             shell=True,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             close_fds=True)
        out, err = p.communicate()
        location = out.decode("utf-8").rstrip('\n')

    except:
        location = 'default'

    return location


def load_modules(dir_path, environment='production', location='default'):
    """
    Loads the modules.yaml file
    """

    modules_file = os.path.join(dir_path, 'modules.yaml')

    if not os.path.isfile(modules_file):
        return {}

    yaml = load_yaml(modules_file)
    locations = yaml['modules']

    try:
        modules = locations[str(location)]
    except:
        err = 'No module configuration for {0}, use default'
        print(err.format(environment))

        modules = locations['default']

    return modules


def deploy_hiera(hiera_dir, hiera_opt='/opt/puppet/hiera'):

    shutil.rmtree(hiera_dir)
    os.symlink(hiera_opt, hiera_dir)


def deploy_modules_vagrant(dir_path, modules, environment='production'):

    #TODO Flexible enough?
    opt_path = '/opt/puppet/modules'
    hiera_dir = os.path.join('/etc/puppetlabs/code/hieradata', environment)

    deploy_hiera(hiera_dir)

    for module in modules.items():
        module_name = module[0]

        if has_opt_module(module_name):
            src = os.path.join(opt_path, module_name)
            dst = dir_path
            os.symlink(src, dst)
        else:
            clone_module(module, dir_path)


def deploy_modules(dir_path, modules, environment='production'):

    for module in modules.items():
        clone_module(module, dir_path)


# TODO Test
def main(is_vagrant=False,
         location='default',
         puppet_dir='/etc/puppetlabs/code/environments/'):

    environments = os.listdir(puppet_dir)
    for environment in environments:

        modules = load_modules(puppet_dir, environment, location)
        dist_dir = os.path.join(puppet_dir, environment, 'dist')
        hiera_dir = os.path.join(puppet_dir, environment, 'dist')
        clear_folder(puppet_dir)

        if is_vagrant:
            deploy_modules_vagrant(dist_dir, modules, environment)
        else:
            deploy_modules(dist_dir, modules)


if __name__ == "__main__":

    is_vagrant = is_vagrant()
    location = get_location()

    main(is_vagrant, location)
