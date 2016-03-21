# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging
from logging.handlers import RotatingFileHandler
from flask import current_app
from eduid_common.api.exceptions import BadConfiguration


__author__ = 'lundberg'


class ApiLogging(object):
    """
    Override the following config settings if needed:
    LOG_FILE = None
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_LEVEL = 'INFO'
    LOG_MAX_BYTES = 1000000
    LOG_BACKUP_COUNT = 10
    """

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('LOG_FILE', None)  # If LOG_FILE is not set skip logging
        app.config.setdefault('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        app.config.setdefault('LOG_LEVEL', 'INFO')
        app.config.setdefault('LOG_MAX_BYTES', 1000000)  # 1 MB
        app.config.setdefault('LOG_BACKUP_COUNT', 10)    # 10 x 1 MB
        app.teardown_appcontext(self.teardown)
        app.extensions.setdefault(self.__class__.__name__, {})
        self.setup_logging()

    def teardown(self, exception):
        pass

    def setup_logging(self):
        app = self.app or current_app
        try:
            if app.config['LOG_FILE']:
                handler = RotatingFileHandler(app.config['LOG_FILE'], maxBytes=app.config['LOG_MAX_BYTES'],
                                              backupCount=app.config['LOG_BACKUP_COUNT'])
                handler.setLevel(app.config['LOG_LEVEL'])
                formatter = logging.Formatter(app.config['LOG_FORMAT'])
                handler.setFormatter(formatter)
                app.logger.addHandler(handler)
                app.logger.info('Logging initiated')
        except AttributeError as e:
            raise BadConfiguration(e.message)






