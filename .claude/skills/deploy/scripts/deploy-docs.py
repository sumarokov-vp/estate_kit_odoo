# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
# ruff: noqa: T201 S603 S607

import os
import subprocess
import sys
from pathlib import Path

import yaml

SITES = {
    "user": {"dir": "docs/user-docs", "remote_subdir": "docs/user"},
    "tech": {"dir": "docs/tech-docs", "remote_subdir": "docs/tech"},
}


def run(cmd: list[str]) -> None:
    print(f"→ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def load_config() -> dict:
    config_path = Path(".claude/devops.yaml")
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    server_name = config["deploy"]["server"]
    server = config["servers"].get(server_name)
    if not server:
        print(f"Server '{server_name}' not found")
        sys.exit(1)

    return server


def build_site(site_dir: str) -> Path:
    site_path = Path(site_dir)
    print(f"\nBuilding {site_path}...")
    run(["uv", "run", "--directory", site_dir, "mkdocs", "build"])
    return site_path / "site"


def deploy_site(built_dir: Path, server: dict, remote_subdir: str, dry_run: bool) -> None:
    host = server["host"]
    user = server["user"]
    key = os.path.expanduser(server["ssh_key"])
    remote_path = server["path"]
    remote_dest = f"{remote_path}/{remote_subdir}/"
    ssh_target = f"{user}@{host}"

    if dry_run:
        print(f"  [DRY RUN] rsync {built_dir}/ → {ssh_target}:{remote_dest}")
        return

    # Ensure remote dir exists
    run(["ssh", "-i", key, ssh_target, f"sudo mkdir -p {remote_dest}"])

    # Rsync built site
    run([
        "rsync", "-avz", "--delete",
        "-e", f"ssh -i {key}",
        f"{built_dir}/",
        f"{ssh_target}:{remote_dest}",
    ])


def reload_caddy(server: dict, dry_run: bool) -> None:
    host = server["host"]
    user = server["user"]
    key = os.path.expanduser(server["ssh_key"])
    remote_path = server["path"]
    ssh_target = f"{user}@{host}"

    if dry_run:
        print("  [DRY RUN] Reload Caddy config")
        return

    # Copy updated Caddyfile
    run([
        "rsync", "-avz",
        "-e", f"ssh -i {key}",
        "docker/Caddyfile",
        f"{ssh_target}:{remote_path}/Caddyfile",
    ])

    # Reload Caddy
    run(["ssh", "-i", key, ssh_target, f"cd {remote_path} && sudo docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile"])


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    site_filter = None
    for i, arg in enumerate(sys.argv):
        if arg == "--site" and i + 1 < len(sys.argv):
            site_filter = sys.argv[i + 1]

    repo_root = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    os.chdir(repo_root)

    server = load_config()

    sites_to_deploy = SITES
    if site_filter:
        if site_filter not in SITES:
            print(f"Site '{site_filter}' not found. Available: {', '.join(SITES.keys())}")
            sys.exit(1)
        sites_to_deploy = {site_filter: SITES[site_filter]}

    for name, site_cfg in sites_to_deploy.items():
        print(f"\n{'='*40}")
        print(f"Deploying: {name}")
        print(f"{'='*40}")

        built_dir = build_site(site_cfg["dir"])
        deploy_site(built_dir, server, site_cfg["remote_subdir"], dry_run)

    reload_caddy(server, dry_run)

    print("\nDocs deployed!")
    for name, site_cfg in sites_to_deploy.items():
        print(f"  https://royalestate.smartist.dev/{site_cfg['remote_subdir']}/")


if __name__ == "__main__":
    main()
