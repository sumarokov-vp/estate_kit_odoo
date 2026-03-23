# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///

import os
import subprocess
import sys
from pathlib import Path

import yaml

IMAGE_TAG = "estate_kit:latest"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print(f"→ {' '.join(cmd)}")
    return subprocess.run(cmd, check=True, **kwargs)


def ssh_cmd(ssh_alias: str, command: str) -> subprocess.CompletedProcess:
    return run(["ssh", ssh_alias, command])


def ssh_output(ssh_alias: str, command: str) -> str:
    result = subprocess.run(
        ["ssh", ssh_alias, command],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def load_config() -> tuple[dict, dict]:
    config_path = Path(".claude/devops.yaml")
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    deploy = config.get("deploy")
    if not deploy:
        print("Missing 'deploy' section in devops.yaml")
        sys.exit(1)

    server_name = deploy["server"]
    servers = config.get("servers", {})
    server = servers.get(server_name)
    if not server:
        print(f"Server '{server_name}' not found in servers")
        sys.exit(1)

    return deploy, server


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    repo_root = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    os.chdir(repo_root)

    deploy, server = load_config()

    container = deploy["container"]
    db_name = deploy["db_name"]

    ssh_alias = server.get("ssh", deploy["server"])
    remote_dir = server["path"]
    src_dir = f"{remote_dir}/src"

    if dry_run:
        print("[DRY RUN] Would execute the following steps:")
        print(f"  1. rsync sources to {ssh_alias}:{src_dir}/")
        print(f"  2. rsync docker configs to {ssh_alias}:{remote_dir}/")
        print(f"  3. Build image on server: docker build -t {IMAGE_TAG}")
        print(f"  4. Deploy: docker compose down + up")
        print(f"  5. Update module: odoo -u estate_kit -d {db_name}")
        print("  6. Restart Odoo and check logs")
        return

    # 1. Create src directory on server
    print(f"Creating {src_dir} on server...")
    ssh_cmd(ssh_alias, f"sudo mkdir -p {src_dir} && sudo chown $(whoami):$(whoami) {src_dir}")

    # 2. Rsync sources (addons + Dockerfile)
    print("Syncing sources to server...")
    run([
        "rsync", "-az", "--delete",
        "--filter=:- .rsyncignore",
        "-e", "ssh",
        "./", f"{ssh_alias}:{src_dir}/",
    ])

    # 3. Rsync docker configs (compose.yaml, Caddyfile)
    print("Syncing docker configs...")
    run([
        "rsync", "-az",
        "-e", "ssh",
        "docker/compose.yaml", "docker/Caddyfile",
        f"{ssh_alias}:{remote_dir}/",
    ])

    # 4. Fetch DB credentials from server
    print("Fetching DB credentials from server...")
    env_content = ssh_output(ssh_alias, f"sudo cat {remote_dir}/.env")
    env_vars = {}
    for line in env_content.splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip()

    db_host = env_vars.get("DB_HOST", "")
    db_port = env_vars.get("DB_PORT", "5432")
    db_user = env_vars.get("DB_USER", "")
    db_password = env_vars.get("DB_PASSWORD", "")

    if not db_password:
        print("ERROR: Could not fetch DB_PASSWORD from server")
        sys.exit(1)

    print(f"DB connection: {db_user}@{db_host}:{db_port}/{db_name}")

    # 5. Build image on server
    print("Building Docker image on server...")
    ssh_cmd(ssh_alias,
            f"sudo docker build -t {IMAGE_TAG} -f {src_dir}/build/Dockerfile {src_dir}")

    # 6. Deploy
    print("Deploying...")
    ssh_cmd(ssh_alias,
            f"bash -c 'cd {remote_dir} && sudo docker compose down && sudo docker compose up -d'")

    # 7. Update module
    print("Updating estate_kit module...")
    ssh_cmd(ssh_alias,
            f"sudo docker exec {container} odoo "
            f"--db_host={db_host} --db_port={db_port} "
            f"--db_user={db_user} --db_password={db_password} "
            f"-d {db_name} -u estate_kit --stop-after-init")

    # 8. Restart Odoo
    print("Restarting Odoo...")
    ssh_cmd(ssh_alias,
            f"bash -c 'cd {remote_dir} && sudo docker compose down odoo && sudo docker compose up -d odoo'")

    # 9. Check logs
    print("Checking logs...")
    ssh_cmd(ssh_alias, f"sudo docker logs --tail 20 {container}")

    print("\nDeploy complete! Site: https://royalestate.smartist.dev/")


if __name__ == "__main__":
    main()
