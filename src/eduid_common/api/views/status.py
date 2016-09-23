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

from flask import json
from flask import Blueprint, current_app, request, abort
import redis

from eduid_userd.db import BaseDB
from eduid_common.session.session import get_redis_pool


status_views = Blueprint('status', __name__, url_prefix='')


def _check_mongo():
    uri = current_app.config['MONGO_URI']
    db = BaseDB(uri, 'eduid_userdb', 'userdb')
    try:
        assert(db.db_count() > 0)
    except:
        return 1
    else:
        db.close()
        return 0

def _check_redis():
    pool = get_redis_pool(current_app.config)
    client = redis.StrictRedis(connection_pool=pool)
    try:
        pong = client.ping()
    except:
        return 1
    else:
        if ping == 'PONG':
            return 0
        return 2


@status_views.route('/smoke-test', methods=['GET'])
def smoke_test():
    m = _check_mongo()
    if m:
        return m
    r = _check_redis()
    if r:
        return r
    return 0


@status_views.route('/sanity-check', methods=['GET'])
def sanity_check():
    pass

