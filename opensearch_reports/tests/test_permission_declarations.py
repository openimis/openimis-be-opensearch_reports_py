"""
Guard rails on opensearch_reports' rights declaration.

Same structure as `core` and `claim`: `DJANGO_PERMS` by entity then by action,
`_PERM_CFG` deriving the config keys from it, and `OpenSearchDashboard.get_rights`
which is only an access point.

What is locked down here:
  * an identifier in one place only (DJANGO_PERMS), hence no drift between the
    declaration and the check;
  * the deployed identifiers (199001 / 199003) and their match with
    `permissions_map.json` - changing one withdraws access from every role that holds
    it;
  * a config key with no class attribute is never loaded by `__load_config` and
    reading it raises AttributeError - the right becomes unenforceable;
  * `has_perms([])` returns True, so an empty list grants to everybody.
"""

import json
import os

from django.test import TestCase

from opensearch_reports.apps import (
    DJANGO_PERMS,
    OpensearchReportsConfig,
    _PERM_CFG,
    configured_perms,
    django_perms,
    perms,
)
from opensearch_reports.models import OpenSearchDashboard

# Les identifiants tels que deployes (cf. migration 0005_add_opensearch_rights).
EXPECTED_RIGHTS = {
    "gql_opensearch_dashboard_search_perms": ["199001"],
    "gql_opensearch_dashboard_update_perms": ["199003"],
}

# The matching `permissions_map.json` entries, by entity/action.
EXPECTED_MAP_ENTRIES = {
    "opensearch_reports.opensearch_dashboard_search": ("openSearchDashboard", "query"),
    "opensearch_reports.opensearch_dashboard_update": ("openSearchDashboard", "update"),
}


def _load_permissions_map():
    """`permissions_map.json` lives in the assembly, not in the package."""
    from django.conf import settings

    candidates = [
        os.path.join(str(settings.BASE_DIR), "permissions_map.json"),
        os.path.join(os.path.dirname(str(settings.BASE_DIR)), "permissions_map.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            with open(path) as handle:
                return json.load(handle)
    return None


class OpenSearchReportsPermissionDeclarationTestCase(TestCase):
    def test_right_ids_unchanged(self):
        self.assertEqual(
            {key: getattr(OpensearchReportsConfig, key) for key in EXPECTED_RIGHTS},
            EXPECTED_RIGHTS,
        )

    def test_perm_cfg_covers_every_declared_action(self):
        declared = {
            (entity, action)
            for entity, actions in DJANGO_PERMS.items()
            for action in actions
        }
        self.assertEqual(set(_PERM_CFG.values()), declared)

    def test_perm_cfg_matches_config_attributes(self):
        """`__load_config` ignores the keys with no class attribute."""
        missing = [key for key in _PERM_CFG if not hasattr(OpensearchReportsConfig, key)]
        self.assertEqual(missing, [])

    def test_no_right_list_is_empty(self):
        empty = [key for key in _PERM_CFG if not getattr(OpensearchReportsConfig, key)]
        self.assertEqual(empty, [])

    def test_attributes_carry_the_declared_right(self):
        for key, (entity, action) in _PERM_CFG.items():
            with self.subTest(key=key):
                self.assertEqual(
                    getattr(OpensearchReportsConfig, key), perms(entity, action)
                )

    def test_no_right_id_is_shared(self):
        """No identifier sharing is intended in this module."""
        seen = {}
        for entity, actions in DJANGO_PERMS.items():
            for action, (_, right_id) in actions.items():
                seen.setdefault(right_id, []).append((entity, action))
        shared = {right: who for right, who in seen.items() if len(who) > 1}
        self.assertEqual(shared, {})

    def test_django_permission_names_are_unique(self):
        seen = {}
        for entity, actions in DJANGO_PERMS.items():
            for action, (name, _) in actions.items():
                seen.setdefault(name, []).append(f"{entity}.{action}")
        shared = {name: who for name, who in seen.items() if len(who) > 1}
        self.assertEqual(shared, {})

    def test_django_permission_names_use_the_app_label(self):
        label = OpenSearchDashboard._meta.app_label
        model = OpenSearchDashboard._meta.model_name
        self.assertEqual(
            django_perms("openSearchDashboard", "query", "update"),
            [f"{label}.view_{model}", f"{label}.change_{model}"],
        )

    def test_unknown_entity_or_action_raises(self):
        with self.assertRaises(KeyError):
            perms("nosuchentity", "query")
        with self.assertRaises(KeyError):
            perms("openSearchDashboard", "nosuchaction")
        with self.assertRaises(KeyError):
            django_perms("openSearchDashboard", "nosuchaction")

    def test_permissions_map_matches_the_declaration(self):
        """The deployed map and the declaration must carry the same integers."""
        mapping = _load_permissions_map()
        if mapping is None:
            self.skipTest("permissions_map.json not found in this assembly")
        for map_key, (entity, action) in EXPECTED_MAP_ENTRIES.items():
            with self.subTest(map_key=map_key):
                self.assertIn(map_key, mapping)
                self.assertEqual(
                    mapping[map_key], str(DJANGO_PERMS[entity][action][1])
                )

    # --- the access point through the model -------------------------------
    def test_model_exposes_every_action_of_its_entity(self):
        for action in DJANGO_PERMS["openSearchDashboard"]:
            with self.subTest(action=action):
                self.assertEqual(
                    OpenSearchDashboard.get_rights(action),
                    configured_perms("openSearchDashboard", action),
                )
                self.assertTrue(OpenSearchDashboard.get_rights(action))

    def test_model_returns_none_for_an_undeclared_action(self):
        """None means "no rule": the caller must fail closed."""
        self.assertIsNone(OpenSearchDashboard.get_rights("nosuchaction"))

    def test_model_reads_the_configured_value_not_the_declared_default(self):
        original = OpensearchReportsConfig.gql_opensearch_dashboard_search_perms
        try:
            OpensearchReportsConfig.gql_opensearch_dashboard_search_perms = ["999999"]
            self.assertEqual(OpenSearchDashboard.get_rights("query"), ["999999"])
            self.assertEqual(perms("openSearchDashboard", "query"), ["199001"])
        finally:
            OpensearchReportsConfig.gql_opensearch_dashboard_search_perms = original
