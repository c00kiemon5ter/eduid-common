#
# Copyright (c) 2016, 2017 NORDUnet A/S
# All rights reserved.
#
#   Redistribution and use in source and binary forms, with or
#   without modification, are permitted provided that the following
#   conditions are met:
#
#     1. Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#     2. Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided
#        with the distribution.
#     3. Neither the name of the NORDUnet nor the names of its
#        contributors may be used to endorse or promote products derived
#        from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
"""
Define a `eduid_init_app` function to create a Flask app and update
it with all attributes common to all eduID services.
"""

from eduid_userdb import UserDB
from eduid_common.api.logging import init_logging
from eduid_common.api.exceptions import init_exception_handlers, init_sentry


def etcd_config(name, app):
    from eduid_common.config.parsers.etcd import EtcdConfigParser

    # Load project wide default settings
    app.config.from_object('eduid_webapp.settings.common')

    try:
        # Load optional app specific default settings
        app.config.from_object('eduid_webapp.{!s}.settings.common'.format(name))
    except ImportError:  # No app specific default config found
        pass

    # Init etcd config parsers
    common_parser = EtcdConfigParser('/eduid/webapp/common/')
    app_parser = EtcdConfigParser('/eduid/webapp/{!s}/'.format(name))

    # Load optional project wide settings
    app.config.update(common_parser.read_configuration(silent = True))
    # Load optional app specific settings
    app.config.update(app_parser.read_configuration(silent = True))


def eduid_init_app(name, config, cfg_func=etcd_config, app=True,
                   userdb=True, sessions=True):
    """
    Create and prepare the flask app for eduID APIs with all the attributes
    common to all apps.

     * Parse and merge configurations
     * Add logging
     * Add db connection
     * Add eduID session

    :param name:     The name of the instance, it will affect the configuration file
                     loaded from the filesystem.
    :param config:   any additional configuration settings. Specially useful
                     in test cases
    :param cfg_func: Callable to initialize config on the application instance
    :param app:      The class used to build the flask app. Should be a
                     descendant of flask.Flask
    :param userdb:   User database, or True for default or False for none
    :param sessions: Session factory class, or True for default or
                     False for none

    :type name:      str
    :type config:    dict
    :type cfg_func:  callable
    :type app:       flask.Flask | bool
    :type sessions:  SessionFactory | bool
    :type userdb:    eduid_userdb.UserDB | bool

    :return: the flask application.
    :rtype: flask.Flask
    """
    if app is True:
        # import here to not drag in dependencies for users supplying
        # their own app_class
        from eduid_common.authn.middleware import AuthnApp
        from werkzeug.contrib.fixers import ProxyFix
        from eduid_common.api.request import Request
        app = AuthnApp(name)
        app.wsgi_app = ProxyFix(app.wsgi_app)
        app.request_class = Request

    if cfg_func:
        cfg_func(name, app)

    # Load optional init time settings
    app.config.update(config)

    # Initialize shared features
    app = init_logging(app)
    app = init_exception_handlers(app)
    app = init_sentry(app)
    if sessions is True:
        from eduid_common.api.session import SessionFactory
        app.session_interface = SessionFactory(app.config)
    elif sessions is not False:
        app.session_interface = sessions

    if userdb is True:
        app.central_userdb = UserDB(app.config['MONGO_URI'], 'eduid_am')  # XXX: Needs updating when we change db
    elif userdb is not False:
        app.central_userdb = userdb

    return app


def eduid_init_app_no_db(name, config, app=True):
    eduid_init_app(name, config, app=app, userdb=False)
