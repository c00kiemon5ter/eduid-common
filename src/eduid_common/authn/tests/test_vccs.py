#
# Copyright (c) 2013, 2014, 2015 NORDUnet A/S
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

from mock import patch
from eduid_userdb.actions.chpass import ChpassUser
from eduid_userdb.testing import MongoTestCase
from eduid_common.authn.testing import TestVCCSClient
from eduid_common.authn import vccs as vccs_module


class VCCSTestCase(MongoTestCase):

    def setUp(self):
        MongoTestCase.setUp(self, None, None)
        self.vccs_client = TestVCCSClient()
        self.central_user = self.amdb.get_user_by_mail('johnsmith@example.com')
        self.user = ChpassUser.from_central_user(self.central_user)
        # Start with no credentials
        for credential in self.user.credentials.to_list():
            self.user.credentials.remove(credential.key)
        vccs_module.add_password(self.user, new_password='abcd', application='test', vccs=self.vccs_client)

    def tearDown(self):
        MongoTestCase.tearDown(self)
        vccs_module.revoke_passwords(self.user, reason='testing', application='test', vccs=self.vccs_client)

    def _check_credentials(self, creds):
        return vccs_module.check_password('dummy', creds, self.user, self.vccs_client)

    def test_check_good_credentials(self):
        result = self._check_credentials('abcd') 
        self.assertTrue(result)

    def test_check_bad_credentials(self):
        result = self._check_credentials('fghi') 
        self.assertFalse(result)

    def test_add_password(self):
        added = vccs_module.add_password(self.user, new_password='wxyz', application='test', vccs=self.vccs_client)
        self.assertTrue(added)
        result1 = self._check_credentials('abcd') 
        self.assertTrue(result1)
        result2 = self._check_credentials('fghi') 
        self.assertFalse(result2)
        result3 = self._check_credentials('wxyz') 
        self.assertTrue(result3)

    def test_change_password(self):
        added = vccs_module.change_password(self.user, new_password='wxyz', old_password='abcd', application='test',
                                            vccs=self.vccs_client)
        self.assertTrue(added)
        result1 = self._check_credentials('abcd') 
        self.assertFalse(result1)
        result2 = self._check_credentials('fghi') 
        self.assertFalse(result2)
        result3 = self._check_credentials('wxyz') 
        self.assertTrue(result3)

    def test_change_password_bad_old_password(self):
        added = vccs_module.change_password(self.user, new_password='wxyz', old_password='fghi', application='test',
                                            vccs=self.vccs_client)
        self.assertFalse(added)
        result1 = self._check_credentials('abcd') 
        self.assertTrue(result1)
        result2 = self._check_credentials('fghi') 
        self.assertFalse(result2)
        result3 = self._check_credentials('wxyz') 
        self.assertFalse(result3)

    def test_reset_password(self):
        added = vccs_module.reset_password(self.user, new_password='wxyz', application='test', vccs=self.vccs_client)
        self.assertTrue(added)
        result1 = self._check_credentials('abcd')
        self.assertFalse(result1)
        result2 = self._check_credentials('fghi')
        self.assertFalse(result2)
        result3 = self._check_credentials('wxyz')
        self.assertTrue(result3)

    def test_change_password_error_adding(self):
        from eduid_common.authn.testing import TestVCCSClient
        with patch.object(TestVCCSClient, 'add_credentials'):
            TestVCCSClient.add_credentials.return_value = False
            added = vccs_module.change_password(self.user, new_password='wxyz', old_password='abcd', application='test',
                                                vccs=self.vccs_client)
            self.assertFalse(added)
            result1 = self._check_credentials('abcd') 
            self.assertTrue(result1)
            result2 = self._check_credentials('fghi') 
            self.assertFalse(result2)
            result3 = self._check_credentials('wxyz') 
            self.assertFalse(result3)

    def test_reset_password_error_revoking(self):
        from eduid_common.authn.testing import TestVCCSClient
        from vccs_client import VCCSClientHTTPError

        def mock_revoke_creds(*args):
            raise VCCSClientHTTPError('dummy', 500)

        with patch.object(TestVCCSClient, 'revoke_credentials', mock_revoke_creds):
            added = vccs_module.reset_password(self.user, new_password='wxyz', application='test',
                                               vccs=self.vccs_client)
            self.assertTrue(added)
            result1 = self._check_credentials('abcd') 
            self.assertFalse(result1)
            result2 = self._check_credentials('fghi') 
            self.assertFalse(result2)
            result3 = self._check_credentials('wxyz') 
            self.assertTrue(result3)


class DeprecatedVCCSTestCase(MongoTestCase):

    def setUp(self):
        MongoTestCase.setUp(self, None, None)
        self.vccs_client = TestVCCSClient()
        self.central_user = self.amdb.get_user_by_mail('johnsmith@example.com')
        self.user = ChpassUser.from_central_user(self.central_user)
        vccs_module.add_credentials('dummy', None, 'abcd', self.user, vccs=self.vccs_client)

    def tearDown(self):
        MongoTestCase.tearDown(self)
        vccs_module.revoke_all_credentials('dummy', self.user, vccs=self.vccs_client)

    def _check_credentials(self, creds):
        return vccs_module.check_password('dummy', creds, self.user, self.vccs_client)

    def test_check_good_credentials(self):
        result = self._check_credentials('abcd')
        self.assertTrue(result)

    def test_check_bad_credentials(self):
        result = self._check_credentials('fghi')
        self.assertFalse(result)

    def test_add_password(self):
        added = vccs_module.add_credentials('dummy', None, 'wxyz', self.user, vccs=self.vccs_client)
        self.assertTrue(added)
        result1 = self._check_credentials('abcd')
        self.assertFalse(result1)
        result2 = self._check_credentials('fghi')
        self.assertFalse(result2)
        result3 = self._check_credentials('wxyz')
        self.assertTrue(result3)

    def test_change_password(self):
        added = vccs_module.add_credentials('dummy', 'abcd', 'wxyz', self.user, vccs=self.vccs_client)
        self.assertTrue(added)
        result1 = self._check_credentials('abcd')
        self.assertFalse(result1)
        result2 = self._check_credentials('fghi')
        self.assertFalse(result2)
        result3 = self._check_credentials('wxyz')
        self.assertTrue(result3)

    def test_change_password_bad_old_password(self):
        added = vccs_module.add_credentials('dummy', 'fghi', 'wxyz', self.user, vccs=self.vccs_client)
        self.assertFalse(added)
        result1 = self._check_credentials('abcd')
        self.assertTrue(result1)
        result2 = self._check_credentials('fghi')
        self.assertFalse(result2)
        result3 = self._check_credentials('wxyz')
        self.assertFalse(result3)

    def test_reset_password(self):
        added = vccs_module.reset_password(self.user, new_password='wxyz', application='test', vccs=self.vccs_client)
        self.assertTrue(added)
        result1 = self._check_credentials('abcd')
        self.assertFalse(result1)
        result2 = self._check_credentials('fghi')
        self.assertFalse(result2)
        result3 = self._check_credentials('wxyz')
        self.assertTrue(result3)

    def test_change_password_error_adding(self):
        from eduid_common.authn.testing import TestVCCSClient
        with patch.object(TestVCCSClient, 'add_credentials'):
            TestVCCSClient.add_credentials.return_value = False
            added = vccs_module.add_credentials('dummy', 'abcd', 'wxyz', self.user, vccs=self.vccs_client)
            self.assertFalse(added)
            result1 = self._check_credentials('abcd')
            self.assertTrue(result1)
            result2 = self._check_credentials('fghi')
            self.assertFalse(result2)
            result3 = self._check_credentials('wxyz')
            self.assertFalse(result3)

    def test_reset_password_error_revoking(self):
        from eduid_common.authn.testing import TestVCCSClient
        from vccs_client import VCCSClientHTTPError

        def mock_revoke_creds(*args):
            raise VCCSClientHTTPError('dummy', 500)

        with patch.object(TestVCCSClient, 'revoke_credentials', mock_revoke_creds):
            added = vccs_module.add_credentials('dummy', None, 'wxyz', self.user, vccs=self.vccs_client)
            self.assertTrue(added)
            result1 = self._check_credentials('abcd')
            self.assertFalse(result1)
            result2 = self._check_credentials('fghi')
            self.assertFalse(result2)
            result3 = self._check_credentials('wxyz')
            self.assertTrue(result3)