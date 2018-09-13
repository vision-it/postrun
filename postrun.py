#!/usr/bin/env python3


"""
The Postrun script is used to either load out Puppet Modules (modules.yaml) from git in production or create symlink to local code in Vagrant
This solves the problem that we don't want use local code for development and remote code in production, also we might have different git remotes in production and
the Puppetfile cannot handle that
"""

import argparse
import concurrent.futures
import logging
import os
import shutil
import subprocess
import sys
import yaml


def create_logger(log_format='%(asctime)s [%(levelname)s]: %(message)s',
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


def mkdir(directory):
    """
    Create a non existing directory.
    """

    os.makedirs(directory, exist_ok=True)


def rmdir(directory):
    """
    Removes a directory or symlink to a directory.
    """

    if os.path.exists(directory):
        if os.path.islink(directory):
            os.remove(directory)
        else:
            shutil.rmtree(directory)


def git(*args):
    """
    Subprocess wrapper for git
    A timeout is set to terminate the process if to response is received.
    For example when the git link is wrong.
    """

    return subprocess.check_call(['git'] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)


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
    except subprocess.CalledProcessError as exp:
        logger.error('Error while cloning {0}'.format(name))
        logger.debug(exp)


def is_vagrant():
    """
    Checks if the current machine runs vagrant.
    """

    return os.path.exists('/vagrant')


def get_location():
    """
    Gets the current location fact for this machine.
    Returns default if nothing is found.
    """

    try:
        cmd = ['/opt/puppetlabs/bin/facter', 'location']
        proc = subprocess.check_output(cmd)
        location = proc.decode("utf-8").rstrip('\n')
    except subprocess.CalledProcessError:
        location = 'default'
    finally:
        if not location:
            location = 'default'

    return location


class ModuleLoader():
    """
    Loads the modules.yaml and returns the modules as dictionary.
    """

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

        self.modules = {}

    def load_modules_file(self):
        """
        Load the modules from the modules file
        """

        if not os.path.isfile(self.modules_file_path):
            self.logger.error('{1} not found for {0}'.format(self.environment, self.modules_file_path))
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
        except KeyError:
            self.logger.info('configuration for location {0} not found, using default'.format(self.location))
            modules = locations['default']

        return modules

    def get_modules(self):
        """
        Returns the modules as a dictionary
        """

        modules = self.load_modules_from_yaml()

        if self.requested_module:

            try:
                module = modules[self.requested_module]

                if self.requested_branch:
                    module['ref'] = self.requested_branch

                modules = {self.requested_module: module}

            except KeyError:
                self.logger.error('Module {0} not found in configuration'.format(self.requested_module))
                modules = {}

        return modules


class ModuleDeployer():
    """
    Deployes the passed modules for Vagrant or on a real machine.
    """

    def __init__(self,
                 dir_path,
                 logger,
                 modules,
                 is_vagrant,
                 hiera_path='/etc/puppetlabs/code/hieradata',
                 opt_path='/opt/puppet/modules',
                 environment='production'):

        self.logger = logger
        self.modules = modules
        self.directory = str(dir_path)
        self.is_vagrant = is_vagrant
        self.opt_path = opt_path
        self.environment = environment
        self.hiera_path = os.path.join(hiera_path, environment)
        self.hiera_opt = '/opt/puppet/hiera'

    def has_opt_module(self, module_name):
        """
        Checks if there is there is a module in /opt.
        Both with dashes and underscores in the name.
        Returns a boolean and the delimiter of the module folders
        """

        module_path_dash = os.path.join(self.opt_path, module_name.replace('_', '-'))
        module_path_underscore = os.path.join(self.opt_path, module_name)

        is_path = os.path.exists(module_path_dash) or os.path.exists(module_path_underscore)
        delimiter = '_' if os.path.exists(module_path_underscore) else '-'

        return (is_path, delimiter)

    def deploy_hiera(self):
        """
        Removes and sets the symlink for the Hiera data in Vagrant.
        """

        rmdir(self.hiera_path)
        os.symlink(self.hiera_opt, self.hiera_path)

    def deploy_local(self, module_name, delimiter):
        """
        Uses /opt symlinks to deploy this module.
        """

        src = os.path.join(self.opt_path, module_name.replace('_', delimiter))
        dst = os.path.join(self.directory, module_name)
        os.symlink(src, dst)

    def deploy_modules(self):
        """
        Loads the modules from either git or sets local symlinks
        """

        # Disabled since we switched to g10k
        # Problem is, that g10k does a shallow clone an removes the .git directory in the hiera repo
        # if self.is_vagrant:
        #     self.deploy_hiera()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for module in self.modules.items():
                module_name = str(module[0])
                module_branch = str(module[1]['ref'])
                module_dir = os.path.join(self.directory, module_name)
                has_opt_path, delimiter = self.has_opt_module(module_name)

                rmdir(module_dir)
                self.logger.debug('Removed {0}'.format(module_dir))

                if self.is_vagrant and has_opt_path:
                    self.logger.debug('Deploying local {0}'.format(module_name))
                    self.deploy_local(module_name, delimiter)
                    # Continue loop since already deployed local
                    continue

                self.logger.debug('Deploying git {0} with branch {1}'.format(module_name, module_branch))
                executor.submit(clone_module(module, self.directory, self.logger))

            executor.shutdown(wait=True)


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
    logger = create_logger(verbose=args.verbose)

    try:
        environments = os.listdir(puppet_base)
    except FileNotFoundError:
        logger.error('%s directory not found', puppet_base)
        sys.exit(1)

    for env in environments:
        logger.info('Postrunning for branch %s', env)

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

        moduledeployer = ModuleDeployer(dir_path=dist_dir,
                                        is_vagrant=is_vagrant,
                                        environment=env,
                                        modules=moduleloader.get_modules(),
                                        logger=logger)

        moduledeployer.deploy_modules()

    # That's all folks
    sys.exit(0)


if __name__ == "__main__":

    ARGS = commandline(sys.argv[1:])
    IS_VAGRANT = is_vagrant()
    LOCATION = get_location()

    main(ARGS, IS_VAGRANT, LOCATION)
