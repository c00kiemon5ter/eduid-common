# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 NORDUnet A/S
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

from __future__ import absolute_import

import redis
from flask import jsonify
from flask import Blueprint, current_app

from eduid_common.session.session import get_redis_pool


status_views = Blueprint('status', __name__, url_prefix='/status')


def _check_mongo():
    db = current_app.central_userdb
    try:
        db.is_healthy()
        return True
    except Exception as exc:
        current_app.logger.warning('Mongodb health check failed: {}'.format(exc))
        return False


def _check_redis():
    pool = get_redis_pool(current_app.config)
    client = redis.StrictRedis(connection_pool=pool)
    try:
        pong = client.ping()
        if pong:
            return True
        current_app.logger.warning('Redis health check failed: response == {!r}'.format(pong))
    except Exception as exc:
        current_app.logger.warning('Redis health check failed: {}'.format(exc))
        return False
    return False


def _check_am():
    try:
        res = current_app.am_relay.ping()
        if res == 'pong for {}'.format(current_app.am_relay.relay_for):
            return True
    except Exception as exc:
        current_app.logger.warning('am health check failed: {}'.format(exc))
        return False
    return False


def _check_msg():
    try:
        res = current_app.msg_relay.ping()
        if res == 'pong':
            return True
    except Exception as exc:
        current_app.logger.warning('msg health check failed: {}'.format(exc))
        return False
    return False


def _check_mail():
    try:
        res = current_app.mail_relay.ping()
        if res == 'pong':
            return True
    except Exception as exc:
        current_app.logger.warning('mail health check failed: {}'.format(exc))
        return False
    return False


@status_views.route('/healthy', methods=['GET'])
def health_check():
    res = {'status': 'STATUS_FAIL'}
    if not _check_mongo():
        res['reason'] = 'mongodb check failed'
        current_app.logger.warning('mongodb check failed')
    elif not _check_redis():
        res['reason'] = 'redis check failed'
        current_app.logger.warning('redis check failed')
    elif getattr(current_app, 'am_relay', False) and not _check_am():
        res['reason'] = 'am check failed'
        current_app.logger.warning('am check failed')
    elif getattr(current_app, 'msg_relay', False) and not _check_msg():
        res['reason'] = 'msg check failed'
        current_app.logger.warning('msg check failed')
    elif getattr(current_app, 'mail_relay', False) and not _check_mail():
        res['reason'] = 'mail check failed'
        current_app.logger.warning('mail check failed')
    else:
        res['status'] = 'STATUS_OK'
        res['reason'] = 'Databases and task queues tested OK'
    return jsonify(res)


@status_views.route('/sanity-check', methods=['GET'])
def sanity_check():
    pass
