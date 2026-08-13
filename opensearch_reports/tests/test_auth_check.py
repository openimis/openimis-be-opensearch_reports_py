from unittest.mock import patch

from core.test_helpers import create_test_interactive_user, create_test_role
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
        cls.role_read = create_test_role(
            ['gql_opensearch_dashboard_search_perms'], name='OpenSearchViewer'
        )
        cls.role_without_right = create_test_role([], name='NoOpenSearchAccess')
        cls.user_allowed = create_test_interactive_user(
            username='os_allowed', roles=[cls.role_read.id]
        )
        cls.user_denied = create_test_interactive_user(
            username='os_denied', roles=[cls.role_without_right.id]
        )

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
