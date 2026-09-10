"""Regression checks for normalized Compose output and rehearsal isolation."""

from copy import deepcopy
import unittest

from check_templates import render, validate


class TemplateIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rehearsal = render(rehearsal=True)

    def test_compose_v2_may_omit_false_bind_options(self):
        config = deepcopy(self.rehearsal)
        for service in config["services"].values():
            for volume in service["volumes"]:
                volume["bind"].pop("create_host_path", None)
        validate(config, rehearsal=True)

    def test_automatic_mount_directory_creation_is_rejected(self):
        config = deepcopy(self.rehearsal)
        config["services"]["postgres"]["volumes"][0]["bind"]["create_host_path"] = True
        with self.assertRaises(AssertionError):
            validate(config, rehearsal=True)

    def test_external_rehearsal_network_is_rejected(self):
        config = deepcopy(self.rehearsal)
        config["networks"]["shop"]["internal"] = False
        with self.assertRaises(AssertionError):
            validate(config, rehearsal=True)

    def test_exposed_database_port_is_rejected(self):
        config = deepcopy(self.rehearsal)
        config["services"]["postgres"]["ports"] = [{"target": 5432, "published": "5432"}]
        with self.assertRaises(AssertionError):
            validate(config, rehearsal=True)


if __name__ == "__main__":
    unittest.main()
