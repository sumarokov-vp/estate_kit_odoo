# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
# ruff: noqa: T201 S603 S607

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


def load_config() -> tuple[str, str]:
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

    ssh_alias = server.get("ssh", server_name)
    remote_path = server.get("path", "/opt/odoo")
    return ssh_alias, remote_path


def build_site(site_dir: str) -> Path:
    site_path = Path(site_dir)
    print(f"\nBuilding {site_path}...")
    run(["uv", "run", "mkdocs", "build", "-f", f"{site_dir}/mkdocs.yml"])
    return site_path / "site"


def deploy_site(built_dir: Path, ssh_alias: str, remote_path: str, remote_subdir: str, dry_run: bool) -> None:
    remote_dest = f"{remote_path}/{remote_subdir}/"

    if dry_run:
        print(f"  [DRY RUN] rsync {built_dir}/ → {ssh_alias}:{remote_dest}")
        return

    run(["ssh", ssh_alias, f"sudo mkdir -p {remote_dest}"])

    run([
        "rsync", "-avz", "--delete",
        "-e", "ssh",
        f"{built_dir}/",
        f"{ssh_alias}:{remote_dest}",
    ])


def reload_caddy(ssh_alias: str, remote_path: str, dry_run: bool) -> None:
    if dry_run:
        print("  [DRY RUN] Reload Caddy config")
        return

    run([
        "rsync", "-avz",
        "-e", "ssh",
        "docker/Caddyfile",
        f"{ssh_alias}:/tmp/Caddyfile",
    ])

    run(["ssh", ssh_alias, f"sudo mv /tmp/Caddyfile {remote_path}/Caddyfile"])

    run(["ssh", ssh_alias, f"cd {remote_path} && sudo docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile"])


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
    import os
    os.chdir(repo_root)

    ssh_alias, remote_path = load_config()

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
        deploy_site(built_dir, ssh_alias, remote_path, site_cfg["remote_subdir"], dry_run)

    reload_caddy(ssh_alias, remote_path, dry_run)

    print("\nDocs deployed!")
    for name, site_cfg in sites_to_deploy.items():
        print(f"  https://royalestate.smartist.dev/{site_cfg['remote_subdir']}/")


if __name__ == "__main__":
    main()
