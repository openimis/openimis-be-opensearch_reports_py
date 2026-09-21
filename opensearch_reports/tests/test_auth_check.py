from unittest.mock import patch

from core.services.userServices import create_or_update_user_roles
from core.test_helpers import (
    create_test_interactive_user,
    create_test_role,
    create_test_technical_user,
)
from django.core.cache import cache
from django.test import TestCase
from graphql_jwt.settings import jwt_settings
from graphql_jwt.shortcuts import get_token
from rest_framework import status
from rest_framework.test import APIClient

from opensearch_reports.apps import OpensearchReportsConfig

AUTH_CHECK_URL = '/api/opensearch_reports/auth_check'


class OpenSearchAuthCheckTest(TestCase):
    """Status contract the nginx auth_request depends on: 200 authorized,
    401 no usable credential (nginx redirects to login), 403 not allowed."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # A core right alongside the module's: the header must not carry it.
        cls.role_read = create_test_role(
            ['gql_opensearch_dashboard_search_perms', 'gql_query_users_perms'],
            name='OpenSearchViewer',
        )
        cls.role_update = create_test_role(
            ['gql_opensearch_dashboard_update_perms'], name='OpenSearchEditor'
        )
        cls.role_without_right = create_test_role([], name='NoOpenSearchAccess')
        cls.user_allowed = create_test_interactive_user(
            username='os_allowed', roles=[cls.role_read.id]
        )
        cls.user_denied = create_test_interactive_user(
            username='os_denied', roles=[cls.role_without_right.id]
        )
        cls.user_editor = create_test_interactive_user(
            username='os_editor', roles=[cls.role_read.id, cls.role_update.id]
        )
        # Passes the gate on the superuser flag while carrying no rights of
        # its own - the one account the administrator branch changes.
        cls.user_tech_admin = create_test_technical_user(
            username='os_tech_admin', super_user=True
        )
        cls.user_tech_admin.is_superuser = True
        cls.user_tech_admin.save()

    def setUp(self):
        # Rights are cached per user with no TTL, so a test that changes roles
        # would leak its cache into the next one after the database rollback.
        cache.clear()

    def _client_for(self, user):
        """Authenticate as the browser does: JWT cookie only, no Authorization
        header, since that is all nginx forwards."""
        client = APIClient()
        client.cookies[jwt_settings.JWT_COOKIE_NAME] = get_token(user)
        return client

    def test_anonymous_request_is_401(self):
        response = APIClient().get(AUTH_CHECK_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_token_is_401(self):
        client = APIClient()
        client.cookies[jwt_settings.JWT_COOKIE_NAME] = 'not-a-jwt'

        response = client.get(AUTH_CHECK_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_whose_user_is_gone_is_401(self):
        # A removed user keeps a usable cookie until it expires.
        client = self._client_for(self.user_allowed)

        with patch('core.jwt_authentication.get_user_by_token', return_value=None):
            response = client.get(AUTH_CHECK_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_without_dashboard_right_is_403(self):
        response = self._client_for(self.user_denied).get(AUTH_CHECK_URL)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_with_dashboard_right_is_200(self):
        response = self._client_for(self.user_allowed).get(AUTH_CHECK_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unconfigured_rights_deny(self):
        with patch.object(OpensearchReportsConfig,
                          'gql_opensearch_dashboard_search_perms', None):
            response = self._client_for(self.user_allowed).get(AUTH_CHECK_URL)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with patch.object(OpensearchReportsConfig,
                          'gql_opensearch_dashboard_search_perms', []):
            response = self._client_for(self.user_allowed).get(AUTH_CHECK_URL)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_check_issues_no_outbound_http(self):
        # nginx invokes this once per Dashboards request, so it must not call out.
        with patch('urllib3.connectionpool.HTTPConnectionPool.urlopen') as pool, \
                patch('requests.Session.request') as session:
            response = self._client_for(self.user_allowed).get(AUTH_CHECK_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pool.assert_not_called()
        session.assert_not_called()

    def test_authorized_response_carries_identity(self):
        response = self._client_for(self.user_allowed).get(AUTH_CHECK_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['X-Auth-User'], 'os_allowed')
        # 199001 only: the role's core right is not the cluster's business.
        self.assertEqual(response['X-Auth-Rights'], '199001')

    def test_rights_header_lists_every_module_right_held(self):
        response = self._client_for(self.user_editor).get(AUTH_CHECK_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['X-Auth-Rights'], '199001,199003')

    def test_technical_superuser_gets_every_module_right(self):
        # It holds no rights at all, so intersecting would hand Dashboards an
        # empty identity for an account the check above just let through.
        response = self._client_for(self.user_tech_admin).get(AUTH_CHECK_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['X-Auth-Rights'], '199001,199003')

    def test_removed_role_drops_its_right(self):
        # The first request caches the rights; the administrator's path closes
        # the user's role rows and drops that cache, so the second recomputes
        # instead of serving what the first one cached.
        client = self._client_for(self.user_editor)
        self.assertEqual(
            client.get(AUTH_CHECK_URL)['X-Auth-Rights'], '199001,199003'
        )

        create_or_update_user_roles(
            self.user_editor.i_user, [self.role_read.id], None
        )

        response = client.get(AUTH_CHECK_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['X-Auth-Rights'], '199001')

    def test_denied_responses_carry_no_identity(self):
        anonymous = APIClient().get(AUTH_CHECK_URL)
        forbidden = self._client_for(self.user_denied).get(AUTH_CHECK_URL)

        self.assertEqual(anonymous.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)
        for response in (anonymous, forbidden):
            self.assertNotIn('X-Auth-User', response)
            self.assertNotIn('X-Auth-Rights', response)
