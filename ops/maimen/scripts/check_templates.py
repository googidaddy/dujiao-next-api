#!/usr/bin/env python3
"""Check effective Compose configuration without creating containers or files."""

import json
import os
from pathlib import Path
import re
import subprocess


DEPLOY = Path(__file__).resolve().parents[1]


def render(rehearsal=False):
    env = dict(os.environ)
    for line in (DEPLOY / ".env.example").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            key, value = line.split("=", 1)
            env[key] = value
    env.update(
        APP_IMAGE="ghcr.io/googidaddy/dujiao-next-fullstack@sha256:" + "1" * 64,
        POSTGRES_PASSWORD="template-check-database-password",
        REDIS_PASSWORD="template-check-redis-password",
    )
    command = [
        "docker", "compose", "--project-directory", str(DEPLOY),
        "-p", "maimen-template-check", "--profile", "app",
        "-f", str(DEPLOY / "compose.yml"),
    ]
    if rehearsal:
        command += ["-f", str(DEPLOY / "compose.rehearsal.yml")]
    result = subprocess.run(
        command + ["config", "--format", "json"], env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    )
    return json.loads(result.stdout)


def validate(config, rehearsal):
    services = config["services"]
    assert set(services) == {"app", "postgres", "redis"}, "Unexpected service"
    assert set(config["networks"]) == {"shop"}, "Unexpected network"
    assert bool(config["networks"]["shop"].get("internal")) == rehearsal
    expected_mounts = {
        "app": {"config/config.yml", "data/uploads", "data/logs"},
        "postgres": {"data/postgres"},
        "redis": {"data/redis"},
    }
    for name, service in services.items():
        assert "container_name" not in service, "Fixed names can collide"
        assert "network_mode" not in service, "No host networking"
        assert not service.get("privileged"), "No privileged containers"
        assert set(service["networks"]) == {"shop"}, "Unexpected egress path"
        assert re.fullmatch(r"[^@\s]+@sha256:[0-9a-f]{64}", service["image"])
        assert service["platform"] == "linux/amd64"
        mounted = set()
        for volume in service["volumes"]:
            assert volume["type"] == "bind"
            source = Path(volume["source"])
            mounted.add(source.relative_to(DEPLOY).as_posix())
            # Compose v2 omits false values from JSON; newer versions retain them.
            assert volume.get("bind", {}).get("create_host_path", False) is False
        assert mounted == expected_mounts[name], "Unexpected mount source"
        if name != "app":
            assert not service.get("ports"), "Data services must stay private"
        if rehearsal:
            assert service["restart"] == "no", "Do not loop failed migrations"
            assert int(service["mem_limit"]) > 0, "Bound shared-host rehearsal memory"
    app = services["app"]
    assert app["profiles"] == ["app"], "Starting data services must not migrate"
    assert app["command"] == ["./dujiao-next", "-mode", "api" if rehearsal else "all"]
    assert len(app["ports"]) == 1
    port = app["ports"][0]
    assert port["host_ip"] == "127.0.0.1" and port["target"] == 8080
    config_mount = next(item for item in app["volumes"] if item["target"] == "/app/config.yml")
    assert config_mount["read_only"] is True


def main():
    for rehearsal in (False, True):
        validate(render(rehearsal), rehearsal)
    print("Compose templates passed: pinned images, private mounts/ports, and rehearsal egress isolation.")


if __name__ == "__main__":
    main()
