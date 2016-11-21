#!/usr/bin/env python3


import argparse
import logging
import os
import shutil
import subprocess
import sys
import threading
import yaml


def Logger(log_format='%(asctime)s [%(levelname)s]: %(message)s',
           log_file='/var/log/postrun.log',
           verbose=False):
    """
    Settings for the logging. Logs are printed to stdout and into a file.
    Returns the logger objects.
    """

    log = logging.getLogger(__name__)
    formatter = logging.Formatter(log_format)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    log.addHandler(stdout_handler)
    log.addHandler(file_handler)

    if verbose:
        log.setLevel(logging.DEBUG)

    return log


def commandline():
    """
    Settings for the commandline arguments.
    Returns the parsed arguments.
    """

    parser = argparse.ArgumentParser(description='Postrun script to deploy Puppet modules via git or locally')

    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
    parser.set_defaults(verbose=False)

    cmd_arguments = parser.parse_args()

    return cmd_arguments


def git(*args):
    """
    Subprocess wrapper for git
    A timeout is set to terminate the process if to response is received.
    For example when the git link is wrong.
    """

    return subprocess.check_call(['git'] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)


def clone_module(module, target_directory, log):
    """
    Clones a git repository.
    Used to get each module.
    """

    name, values = module
    url = values['url']
    ref = values['ref']
    target = os.path.join(target_directory, name)

    try:
        git('clone', url, '-b', ref, target)
    except:
        log.error('Error while cloning {0}'.format(name))


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
    Checks if there is there is a module in /opt.
    Both with dashes and underscores in the name.
    Returns a boolean and the delimiter of the module folders
    """

    module_path_dash = os.path.join(opt_path, module_name.replace('_', '-'))
    module_path_underscore = os.path.join(opt_path, module_name)

    is_path = os.path.exists(module_path_dash) or os.path.exists(module_path_underscore)
    delimiter = '_' if os.path.exists(module_path_underscore) else '-'

    return (is_path, delimiter)


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


def load_modules(dir_path, log, environment='production', location='default'):
    """
    Loads the modules.yaml file
    """

    modules_file = os.path.join(dir_path, environment, 'modules.yaml')

    if not os.path.isfile(modules_file):
        log.error('No modules.yaml found for {0}'.format(environment))
        return {}

    yaml = load_yaml(modules_file)
    locations = yaml['modules']

    try:
        modules = locations[str(location)]
    except:
        log.warn('No module configuration for {0}, use default'.format(location))
        modules = locations['default']

    return modules


def deploy_hiera(hiera_dir, hiera_opt='/opt/puppet/hiera'):
    """
    Removes and sets the symlink for the Hiera data in Vagrant.
    """

    if os.path.islink(hiera_dir):
        os.remove(hiera_dir)
    else:
        shutil.rmtree(hiera_dir)

    os.symlink(hiera_opt, hiera_dir)


def deploy_modules_vagrant(dir_path,
                           modules,
                           log,
                           hiera_path='/etc/puppetlabs/code/hieradata',
                           opt_path='/opt/puppet/modules',
                           environment='production'):
    """
    Deploys all modules in a Vagrant installation.
    Uses symlinks for modules present in /opt
    """

    threads = []
    hiera_dir = os.path.join(hiera_path, environment)

    deploy_hiera(hiera_dir)

    for module in modules.items():
        module_name = str(module[0])
        has_opt, delimiter = has_opt_module(module_name)

        if has_opt:
            log.debug('Deploying local {0}'.format(module_name))

            src = os.path.join(opt_path, module_name.replace('_', delimiter))
            dst = os.path.join(dir_path, module_name)
            os.symlink(src, dst)

        else:
            log.debug('Deploying git {0}'.format(module_name))

            t = threading.Thread(target=clone_module, args=(module, dir_path, log))
            threads.append(t)
            t.start()


def deploy_modules(dir_path, modules, log, environment='production'):
    """
    Deploys all modules passed via git.
    """

    threads = []

    for module in modules.items():
        module_name = str(module[0])
        log.debug('Deploying git {0}'.format(module_name))

        t = threading.Thread(target=clone_module, args=(module, dir_path, log))
        threads.append(t)
        t.start()


def main(args,
         is_vagrant=False,
         location='default',
         puppet_base='/etc/puppetlabs/code/environments/',
         hiera_base='/etc/puppetlabs/code/hieradata',):

    """
    Where the magic happens.
    """

    logger = Logger(verbose=args.verbose)
    environments = os.listdir(puppet_base)

    for environment in environments:

        modules = load_modules(dir_path=puppet_base,
                               environment=environment,
                               location=location,
                               log=logger)

        dist_dir = os.path.join(puppet_base, environment, 'dist')
        hiera_dir = os.path.join(hiera_base, environment)

        clear_folder(dist_dir)

        if is_vagrant:
            deploy_modules_vagrant(dir_path=dist_dir, modules=modules, environment=environment, log=logger)
        else:
            deploy_modules(dir_path=dist_dir, modules=modules, log=logger)


if __name__ == "__main__":

    args = commandline()
    is_vagrant = is_vagrant()
    location = get_location()

    main(args, is_vagrant, location)
