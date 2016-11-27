[![Build Status](https://travis-ci.org/vision-it/postrun.svg?branch=master)](https://travis-ci.org/vision-it/postrun) [![Coverage Status](https://coveralls.io/repos/github/vision-it/postrun/badge.svg?branch=master)](https://coveralls.io/github/vision-it/postrun?branch=master)

# Postrun
Deploys Puppet modules from modules.yaml

# Prerequisite

## Vagrant
To deploy local modules and Hiera data in Vagrant the files need to places under:

- */opt/puppet/modules*
- */opt/puppet/hiera*

## modules.yaml
The postrun script requires a modules.yaml file for each environment in */etc/puppetlabs/code/environments/environment_name/modules.yaml*

The modules.yaml file lists a *location* and the Puppet modules for this location. Example:

```
modules:
  location_name:
    module_name:
      url: 'https://github.com/foobar.git'
      ref: branch'
```

# Usage

Getting help:
```bash
/etc/puppetlabs/r10k/postrun/postrun.py -h
```

Running the postrun script:
```bash
/etc/puppetlabs/r10k/postrun/postrun.py
```

Running the postrun script verbose:
```bash
/etc/puppetlabs/r10k/postrun/postrun.py -v
```

## Logging

The script writes all messages to stdout and into a logfile */var/log/postrun.log*.

# Testing and Development

Installing requirements:
```bash
pip install -r tests/requirements.txt
```

Running tests:
```bash
py.test
```

Running tests with coverage:
```bash
py.test --cov=postrun tests/
```
