# -*- coding: utf-8 -*-

import os
import os.path
import sys
import etcd
import yaml
import json
try:
    import ConfigParser as configparser
except ImportError:
    # Python 3
    import configparser

__author__ = 'lundberg'


class IniConfigParser(object):

    def __init__(self, config_file_name, config_environment_variable=None):
        """
        :param config_file_name: config files name
        :type config_file_name: str | unicode
        :param config_environment_variable: Optional env variable to read config from
        :type config_environment_variable: str | unicode
        :return: IniConfigParser object
        :rtype: IniConfigParser
        """
        self.config_file_name = config_file_name
        self.config_environment_variable = config_environment_variable
        self.known_special_keys = {
            # <var name>.lower(): (<read function>, <default>),
            'celery_accept_content': (self.read_list, ['application/json']),
        }

    def get_config_file(self):
        """Get the configuration file looking for it in several places.

        The lookup order is:
        1. A file named according to the value of the config_environment_variable env variable
        2. A file named config_file_name In the current working directory
        3. A file named .config_file_name in the user's home directory
        4. A file named config_file_name in the system configuration directory (/etc)
        """
        file_name = os.environ.get(self.config_environment_variable, self.config_file_name)

        if os.path.exists(file_name):
            return file_name

        user_file = os.path.expanduser(
            os.path.join('~', '.', self.config_file_name))
        if os.path.exists(user_file):
            return user_file

        global_file = os.path.join('/etc', self.config_file_name)
        if os.path.exists(global_file):
            return global_file

    def read_setting_from_env(self, settings, key, default=None):
        env_variable = key.upper()
        if env_variable in os.environ:
            return os.environ[env_variable]
        else:
            return settings.get(key, default)

    def read_setting_from_env_bool(self, settings, key, default=None):
        value = self.read_setting_from_env(settings, key, '').lower()
        if value == 'false':
            return False
        if value == 'true':
            return True
        return default

    def read_mapping(self, settings, prop, available_keys=None, default=None, required=True):
        raw = self.read_setting_from_env(settings, prop, '')

        if raw.strip() == '':
            return default

        rows = raw.strip('\n ').split('\n')

        mapping = {}

        for row in rows:
            splitted_row = row.split('=')
            key = splitted_row[0].strip()
            if len(splitted_row) > 1:
                value = splitted_row[1].strip()
            else:
                value = ''
            if available_keys is None or key in available_keys:
                mapping[key] = value

        if available_keys is not None:
            if len(mapping.keys()) != len(available_keys) and 'testing' not in settings:
                return None

        return mapping

    def read_list(self, settings, prop, default=list()):
        raw = self.read_setting_from_env(settings, prop, None)
        if raw is None or raw.strip() == '':
            return default

        return [e for e in raw.split('\n') if e is not None and e.strip() != '']

    def read_configuration(self):
        """
        Read the settings from environment or .ini file and return them as a dict

        The values are decoded as JSON, or used as-is if they can't be decoded as JSON.
        """
        settings = {}

        config_file = self.get_config_file()
        if config_file is not None:
            config = configparser.RawConfigParser()
            config.read(config_file)

            if config.has_section('main'):
                for key, val in config.items('main'):
                    if key in self.known_special_keys:
                        func, default = self.known_special_keys[key]
                    else:
                        func = self.read_setting_from_env
                        default = ''
                    settings[key.upper()] = func({key: val}, key, default=default)

        return settings


class EtcdConfigParser(object):

    def __init__(self, namespace, host=None, port=None):
        """
        :param namespace: etcd name space to read or write
        :type namespace: str | unicode
        :param host: Optional etcd host
        :type host: str | unicode
        :param port: Optional etcd port
        :type port: int
        :return: EtcdConfigParser object
        :rtype: EtcdConfigParser
        """
        if not host:
            host = os.environ.get('ETCD_HOST', '127.0.0.1')
        if not port:
            port = int(os.environ.get('ETCD_PORT', '2379'))
        self.ns = namespace
        self.client = etcd.Client(host, port)

    def read_configuration(self):
        settings = {}
        for child in self.client.read(self.ns, recursive=True).children:
            # Remove namespace and uppercase the key
            key = child.key.lstrip(self.ns).upper()
            # Load etcd string with json to handle complex structures
            settings[key] = json.loads(child.value)
        return settings

    def write_configuration(self, config):
        # Remove first and last slash and create key hierarchy
        ns_keys = self.ns.lstrip('/').rstrip('/').split('/')
        # Recurse to last key
        for key in ns_keys:
            config = config[key]
        # Write keys and values to etcd
        for key, value in config.items():
            fq_key = '{!s}{!s}'.format(self.ns, key)
            json_value = json.dumps(value)
            self.client.write(fq_key, json_value)

    def write_configuration_from_yaml_file(self, file_path):
        with open(file_path) as f:
            config = yaml.load(f)
            if not config:
                sys.stderr.writelines('No YAML found in {!s}\n'.format(file_path))
                sys.exit(1)
            self.write_configuration(config)




