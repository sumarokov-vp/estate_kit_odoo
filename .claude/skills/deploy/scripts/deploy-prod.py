import os
import subprocess
import sys
from pathlib import Path

import yaml


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print(f"→ {' '.join(cmd)}")
    return subprocess.run(cmd, check=True, **kwargs)


def ssh_cmd(ssh_opts: list[str], target: str, command: str) -> subprocess.CompletedProcess:
    return run(["ssh", *ssh_opts, target, command])


def ssh_output(ssh_opts: list[str], target: str, command: str) -> str:
    result = subprocess.run(
        ["ssh", *ssh_opts, target, command],
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

    image = deploy["image"]
    container = deploy["container"]
    db_name = deploy["db_name"]
    dockerfile = deploy.get("dockerfile", "build/Dockerfile")

    host = server["host"]
    user = server["user"]
    key = os.path.expanduser(server["ssh_key"])
    remote_dir = server["path"]

    ssh_opts = ["-i", key, "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=no"]
    ssh_target = f"{user}@{host}"

    if dry_run:
        print("[DRY RUN] Would execute the following steps:")
        print(f"  1. Build image: docker build --platform linux/amd64 -t {image} -f {dockerfile} .")
        print(f"  2. Push image: docker push {image}")
        print(f"  3. SSH deploy on {ssh_target}: pull + down + up")
        print(f"  4. Update module: odoo -u estate_kit -d {db_name}")
        print(f"  5. Restart Odoo and check logs")
        return

    # 1. Fetch DB credentials from server
    print("Fetching DB credentials from server...")
    env_content = ssh_output(ssh_opts, ssh_target, f"cat {remote_dir}/.env")
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

    # 2. Build image
    print("Building Docker image (AMD64)...")
    run([
        "docker", "build", "--no-cache", "--platform", "linux/amd64",
        "-t", image,
        "-f", dockerfile,
        ".",
    ])

    # 3. Push image
    print("Pushing image to registry...")
    run(["docker", "push", image])

    # 4. Deploy on server
    print("Deploying on server...")
    ssh_cmd(ssh_opts, ssh_target,
            f"cd {remote_dir} && docker compose pull && docker compose down && docker compose up -d")

    # 5. Update module
    print("Updating estate_kit module...")
    ssh_cmd(ssh_opts, ssh_target,
            f"docker exec {container} odoo "
            f"--db_host={db_host} --db_port={db_port} "
            f"--db_user={db_user} --db_password={db_password} "
            f"-d {db_name} -u estate_kit --stop-after-init")

    # 6. Restart Odoo
    print("Restarting Odoo...")
    ssh_cmd(ssh_opts, ssh_target, f"cd {remote_dir} && docker compose restart odoo")

    # 7. Check logs
    print("Checking logs...")
    ssh_cmd(ssh_opts, ssh_target, f"docker logs --tail 20 {container}")

    print("\nDeploy complete! Site: https://royalestate.smartist.dev/")


if __name__ == "__main__":
    main()
