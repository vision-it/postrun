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


def commandline(args):
    """
    Settings for the commandline arguments.
    Returns the parsed arguments.
    """

    parser = argparse.ArgumentParser(description='Postrun script to deploy Puppet modules via git or locally')

    parser.add_argument("-v", "--verbose",
                        help="increase output verbosity",
                        action="store_true")

    parser.add_argument("-m", "--module",
                        help="Name of the module to deploy")

    parser.add_argument("-b", "--branch",
                        help="Branch to deploy for a single module")

    parser.set_defaults(verbose=False)

    return parser.parse_args(args)


def threaded(func):
    """
    Multithreading function decorator
    """

    def run(*args, **kwargs):

        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()

        return thread

    return run


def rmdir(directory):
    """
    Removes a directory or symlink to a directory.
    """

    if os.path.exists(directory):
        if os.path.islink(directory):
            os.remove(directory)
        else:
            shutil.rmtree(directory)

def mkdir(directory):
    """
    Create a non existing directory.
    """

    if not os.path.exists(directory):
        os.makedirs(directory)


def git(*args):
    """
    Subprocess wrapper for git
    A timeout is set to terminate the process if to response is received.
    For example when the git link is wrong.
    """

    return subprocess.check_call(['git'] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)


@threaded
def clone_module(module, target_directory, logger):
    """
    Clones a git repository.
    Used to get each module.
    """

    name, values = module
    url = values['url']
    ref = values['ref']
    target = os.path.join(target_directory, name)

    try:
        git('clone', '--depth', '1', url, '-b', ref, target)
    except:
        logger.error('Error while cloning {0}'.format(name))


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
        cmd = ['/opt/puppetlabs/bin/facter', 'location']
        p = subprocess.check_output(cmd)
        location = p.decode("utf-8").rstrip('\n')

    except:
        location = 'default'

    return location


class ModuleLoader():

    def __init__(self,
                 dir_path,
                 logger,
                 environment='production',
                 location='default',
                 module=None,
                 branch=None):


        self.requested_module = module
        self.requested_branch = branch
        self.logger = logger
        self.directory = str(dir_path)
        self.environment = str(environment)
        self.location = str(location)
        self.modules_file_path = os.path.join(dir_path, environment, 'modules.yaml')

        self.modules = self.load_modules_from_yaml()

    def load_modules_file(self):
        """
        Load the modules from the modules file
        """

        if not os.path.isfile(self.modules_file_path):
            self.logger.error('{0} not found for {1}'.format(self.environment, self.modules_file_path))
            return {}

        with open(self.modules_file_path, 'r') as yaml_file:
            parsed_yaml = yaml.load(yaml_file)

        return parsed_yaml

    def load_modules_from_yaml(self):
        """
        Get modules for the specified location
        """

        modules = {}

        try:
            yaml = self.load_modules_file()
            locations = yaml['modules']
            modules = locations[self.location]

        except:
            self.logger.warn('configuration for location {0} not found, using default'.format(self.location))
            modules = locations['default']

        finally:
            return modules

    def get_modules(self):
        """
        Returns the modules as a dictionary
        """

        modules = self.modules

        if self.requested_module:

            try:
                module = modules[self.requested_module]

                if self.requested_branch:
                    module['ref'] = self.requested_branch

                modules = {self.requested_module: module}

            except:
                self.logger.error('Module {0} not found in'.format(self.requested_module))
                modules = {}

        return modules


def deploy_hiera(hiera_dir, hiera_opt='/opt/puppet/hiera'):
    """
    Removes and sets the symlink for the Hiera data in Vagrant.
    """

    rmdir(hiera_dir)
    os.symlink(hiera_opt, hiera_dir)


def deploy_modules_vagrant(dir_path,
                           modules,
                           logger,
                           hiera_path='/etc/puppetlabs/code/hieradata',
                           opt_path='/opt/puppet/modules',
                           environment='production'):
    """
    Deploys all modules in a Vagrant installation.
    Uses symlinks for modules present in /opt
    """

    hiera_dir = os.path.join(hiera_path, environment)
    deploy_hiera(hiera_dir)

    for module in modules.items():
        module_name = str(module[0])
        module_branch = str(module[1]['ref'])
        module_dir = os.path.join(dir_path, module_name)
        has_opt_path, delimiter = has_opt_module(module_name)

        rmdir(module_dir)

        if has_opt_path:
            logger.debug('Deploying local {0}'.format(module_name))

            src = os.path.join(opt_path, module_name.replace('_', delimiter))
            dst = os.path.join(dir_path, module_name)
            os.symlink(src, dst)

        else:
            logger.debug('Deploying git {0} with branch {1}'.format(module_name, module_branch))
            clone_module(module, dir_path, logger)


def deploy_modules(dir_path,
                   modules,
                   logger,
                   environment='production'):
    """
    Deploys all modules passed via git.
    """

    for module in modules.items():
        module_name = str(module[0])
        module_branch = str(module[1]['ref'])
        module_dir = os.path.join(dir_path, module_name)

        logger.debug('Deploying git {0} with branch {1}'.format(module_name, module_branch))

        rmdir(module_dir)
        clone_module(module, dir_path, logger)


def main(args,
         is_vagrant=False,
         location='default',
         puppet_base='/etc/puppetlabs/code/environments/',
         hiera_base='/etc/puppetlabs/code/hieradata'):

    """
    Where the magic happens.
    """

    module = args.module
    branch = args.branch
    logger = Logger(verbose=args.verbose)

    try:
        environments = os.listdir(puppet_base)
    except:
        logger.error('{0} directory not found'.format(puppet_base))
        sys.exit(2)

    for env in environments:
        dist_dir = os.path.join(puppet_base, env, 'dist')
        mkdir(dist_dir)

        hiera_dir = os.path.join(hiera_base, env)
        mkdir(hiera_dir)

        moduleloader = ModuleLoader(dir_path=puppet_base,
                                    environment=env,
                                    location=location,
                                    logger=logger,
                                    module=module,
                                    branch=branch)

        modules = moduleloader.modules

        if is_vagrant:
            deploy_modules_vagrant(dir_path=dist_dir,
                                   environment=env,
                                   modules=modules,
                                   logger=logger)

        else:
            deploy_modules(dir_path=dist_dir,
                           environment=env,
                           modules=modules,
                           logger=logger)

    # That's all folks
    sys.exit(0)


if __name__ == "__main__":

    args = commandline(sys.argv[1:])
    is_vagrant = is_vagrant()
    location = get_location()

    main(args, is_vagrant, location)
