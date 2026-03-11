#!/usr/bin/env python3
"""Manage NAS files over SFTP/FTP/FTPS.

Commands:
- upload
- download
- delete
- list
"""

from __future__ import annotations

import argparse
import ftplib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import stat
import sys
from urllib.parse import urlparse

from dotenv import load_dotenv
import paramiko


def load_environment() -> None:
    env_path = Path(__file__).with_name(".env")
    load_dotenv(dotenv_path=env_path, override=False)


def die(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def normalize_remote(root: str, remote: str) -> str:
    remote_clean = remote.replace("\\", "/")
    base = PurePosixPath(root or "/")
    target = (base / remote_clean).as_posix() if not remote_clean.startswith("/") else PurePosixPath(remote_clean).as_posix()
    return target


def parse_endpoint(raw_host: str, raw_port: int | None, explicit_protocol: str | None) -> tuple[str, str, int]:
    """Parse protocol/host/port from CLI and env values."""
    host_value = (raw_host or "").strip()
    if not host_value:
        die("Host is required: use --host or SFTP_HOST/FTP_HOST")

    protocol_hint = (explicit_protocol or "").strip().lower()
    if protocol_hint and protocol_hint not in {"sftp", "ftp", "ftps"}:
        die(f"Unsupported protocol: {protocol_hint}. Use sftp, ftp, or ftps.")

    if "://" in host_value:
        parsed = urlparse(host_value)
        scheme = (parsed.scheme or "").lower()
        host = parsed.hostname or ""
        port = raw_port or parsed.port

        if scheme == "ssh":
            scheme = "sftp"
        if scheme and scheme not in {"sftp", "ftp", "ftps"}:
            die(f"Unsupported endpoint scheme: {scheme}. Use sftp://, ftp://, or ftps://")
        if protocol_hint and scheme and protocol_hint != scheme:
            die(f"Protocol mismatch: --protocol={protocol_hint} but endpoint uses {scheme}://")

        if not host:
            die(f"Invalid endpoint: {host_value}")

        protocol = scheme or protocol_hint or "sftp"
        if protocol == "sftp":
            return protocol, host, int(port or 22)
        if protocol == "ftps":
            return protocol, host, int(port or 21)
        return protocol, host, int(port or 21)

    if protocol_hint:
        protocol = protocol_hint
    elif raw_port == 21:
        protocol = "ftp"
    elif raw_port == 990:
        protocol = "ftps"
    else:
        protocol = "sftp"

    if protocol == "sftp":
        return protocol, host_value, int(raw_port or 22)
    if protocol == "ftps":
        return protocol, host_value, int(raw_port or 21)
    return protocol, host_value, int(raw_port or 21)


def connect(args: argparse.Namespace) -> tuple[str, object, object]:
    host_raw = args.host or os.getenv("SFTP_HOST") or os.getenv("FTP_HOST")
    port_raw = args.port or os.getenv("SFTP_PORT") or os.getenv("FTP_PORT")
    protocol_raw = args.protocol or os.getenv("FILE_PROTOCOL")
    user = args.user or os.getenv("SFTP_USER") or os.getenv("FTP_USER")
    password = args.password or os.getenv("SFTP_PASSWORD") or os.getenv("FTP_PASSWORD")
    key_file = args.key_file or os.getenv("SFTP_KEY_FILE")
    key_passphrase = args.key_passphrase or os.getenv("SFTP_KEY_PASSPHRASE")

    protocol, host, port = parse_endpoint(host_raw or "", int(port_raw) if port_raw else None, protocol_raw)

    if not user:
        die("Username is required: use --user or SFTP_USER/FTP_USER")

    if protocol == "sftp":
        if not password and not key_file:
            die("SFTP requires password or key file: --password/--key-file or SFTP_PASSWORD/SFTP_KEY_FILE")

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh_client.connect(
                hostname=host,
                port=port,
                username=user,
                password=password,
                key_filename=key_file,
                passphrase=key_passphrase,
                timeout=15,
                banner_timeout=15,
                auth_timeout=15,
                look_for_keys=False,
                allow_agent=False,
            )
            sftp = ssh_client.open_sftp()
        except Exception as exc:  # noqa: BLE001
            ssh_client.close()
            die(f"Failed to connect with SFTP: {exc}")
        return protocol, ssh_client, sftp

    if not password:
        die("FTP/FTPS requires password: use --password or FTP_PASSWORD/SFTP_PASSWORD")

    ftp_client: ftplib.FTP
    if protocol == "ftps":
        ftp_client = ftplib.FTP_TLS()
    else:
        ftp_client = ftplib.FTP()

    try:
        ftp_client.connect(host=host, port=port, timeout=15)
        ftp_client.login(user=user, passwd=password)
        if protocol == "ftps":
            assert isinstance(ftp_client, ftplib.FTP_TLS)
            ftp_client.prot_p()
    except Exception as exc:  # noqa: BLE001
        try:
            ftp_client.close()
        except Exception:  # noqa: BLE001
            pass
        die(f"Failed to connect with {protocol.upper()}: {exc}")

    return protocol, ftp_client, ftp_client


def ensure_remote_dir(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    parts = [p for p in PurePosixPath(remote_dir).parts if p not in ("", "/")]
    current = "/" if remote_dir.startswith("/") else ""
    for part in parts:
        current = f"{current}/{part}" if current else part
        try:
            st = sftp.stat(current)
            if not stat.S_ISDIR(st.st_mode):
                die(f"Remote path exists but is not a directory: {current}")
        except FileNotFoundError:
            sftp.mkdir(current)


def ftp_is_dir(ftp: ftplib.FTP, remote_path: str) -> bool:
    original_dir = ftp.pwd()
    try:
        ftp.cwd(remote_path)
        return True
    except ftplib.error_perm:
        return False
    finally:
        try:
            ftp.cwd(original_dir)
        except ftplib.error_perm:
            pass


def ftp_size_or_none(ftp: ftplib.FTP, remote_path: str) -> int | None:
    try:
        size = ftp.size(remote_path)
        return int(size) if size is not None else None
    except (ftplib.error_perm, ValueError):
        return None


def ftp_exists(ftp: ftplib.FTP, remote_path: str) -> bool:
    if ftp_is_dir(ftp, remote_path):
        return True
    if ftp_size_or_none(ftp, remote_path) is not None:
        return True
    return False


def ftp_ensure_remote_dir(ftp: ftplib.FTP, remote_dir: str) -> None:
    parts = [p for p in PurePosixPath(remote_dir).parts if p not in ("", "/")]
    current = "/" if remote_dir.startswith("/") else ""
    for part in parts:
        current = f"{current}/{part}" if current else part
        if ftp_is_dir(ftp, current):
            continue
        try:
            ftp.mkd(current)
        except ftplib.error_perm:
            if not ftp_is_dir(ftp, current):
                die(f"Cannot create remote directory: {current}")


def ftp_upload_file(ftp: ftplib.FTP, local_file: Path, remote_file: str) -> None:
    parent = str(PurePosixPath(remote_file).parent)
    if parent and parent != ".":
        ftp_ensure_remote_dir(ftp, parent)
    with local_file.open("rb") as handle:
        ftp.storbinary(f"STOR {remote_file}", handle)


def ftp_upload_dir_recursive(ftp: ftplib.FTP, local_dir: Path, remote_dir: str) -> None:
    ftp_ensure_remote_dir(ftp, remote_dir)
    for child in local_dir.iterdir():
        remote_child = str(PurePosixPath(remote_dir) / child.name)
        if child.is_dir():
            ftp_upload_dir_recursive(ftp, child, remote_child)
        else:
            ftp_upload_file(ftp, child, remote_child)


def ftp_download_file(ftp: ftplib.FTP, remote_file: str, local_file: Path) -> None:
    local_file.parent.mkdir(parents=True, exist_ok=True)
    with local_file.open("wb") as handle:
        ftp.retrbinary(f"RETR {remote_file}", handle.write)


def ftp_list_names(ftp: ftplib.FTP, remote_dir: str) -> list[str]:
    try:
        return [name for name, _ in ftp.mlsd(remote_dir) if name not in (".", "..")]
    except (AttributeError, ftplib.error_perm):
        original_dir = ftp.pwd()
        try:
            ftp.cwd(remote_dir)
            return [name for name in ftp.nlst() if name not in (".", "..")]
        finally:
            ftp.cwd(original_dir)


def ftp_download_dir_recursive(ftp: ftplib.FTP, remote_dir: str, local_dir: Path) -> None:
    local_dir.mkdir(parents=True, exist_ok=True)
    for name in ftp_list_names(ftp, remote_dir):
        remote_child = posixpath.join(remote_dir.rstrip("/"), name) if remote_dir != "/" else f"/{name}"
        local_child = local_dir / name
        if ftp_is_dir(ftp, remote_child):
            ftp_download_dir_recursive(ftp, remote_child, local_child)
        else:
            ftp_download_file(ftp, remote_child, local_child)


def ftp_delete_recursive(ftp: ftplib.FTP, remote_path: str) -> None:
    if ftp_is_dir(ftp, remote_path):
        for name in ftp_list_names(ftp, remote_path):
            child = posixpath.join(remote_path.rstrip("/"), name) if remote_path != "/" else f"/{name}"
            ftp_delete_recursive(ftp, child)
        ftp.rmd(remote_path)
    else:
        ftp.delete(remote_path)


def ftp_list_items(ftp: ftplib.FTP, remote_dir: str) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    try:
        for name, facts in ftp.mlsd(remote_dir):
            if name in (".", ".."):
                continue
            item_type = "dir" if facts.get("type") == "dir" else "file"
            raw_size = facts.get("size")
            item_size = None
            if item_type == "file" and raw_size and str(raw_size).isdigit():
                item_size = int(raw_size)
            items.append({"name": name, "type": item_type, "size": item_size})
    except (AttributeError, ftplib.error_perm):
        for name in ftp_list_names(ftp, remote_dir):
            remote_child = posixpath.join(remote_dir.rstrip("/"), name) if remote_dir != "/" else f"/{name}"
            is_dir = ftp_is_dir(ftp, remote_child)
            items.append(
                {
                    "name": name,
                    "type": "dir" if is_dir else "file",
                    "size": None if is_dir else ftp_size_or_none(ftp, remote_child),
                }
            )

    return sorted(items, key=lambda x: str(x["name"]).lower())


def upload_file(sftp: paramiko.SFTPClient, local_file: Path, remote_file: str) -> None:
    parent = str(PurePosixPath(remote_file).parent)
    if parent and parent != ".":
        ensure_remote_dir(sftp, parent)
    sftp.put(str(local_file), remote_file)


def upload_dir_recursive(sftp: paramiko.SFTPClient, local_dir: Path, remote_dir: str) -> None:
    ensure_remote_dir(sftp, remote_dir)
    for child in local_dir.iterdir():
        remote_child = str(PurePosixPath(remote_dir) / child.name)
        if child.is_dir():
            upload_dir_recursive(sftp, child, remote_child)
        else:
            upload_file(sftp, child, remote_child)


def download_file(sftp: paramiko.SFTPClient, remote_file: str, local_file: Path) -> None:
    local_file.parent.mkdir(parents=True, exist_ok=True)
    sftp.get(remote_file, str(local_file))


def download_dir_recursive(sftp: paramiko.SFTPClient, remote_dir: str, local_dir: Path) -> None:
    local_dir.mkdir(parents=True, exist_ok=True)
    for item in sftp.listdir_attr(remote_dir):
        remote_child = str(PurePosixPath(remote_dir) / item.filename)
        local_child = local_dir / item.filename
        if stat.S_ISDIR(item.st_mode):
            download_dir_recursive(sftp, remote_child, local_child)
        else:
            download_file(sftp, remote_child, local_child)


def delete_remote_recursive(sftp: paramiko.SFTPClient, remote_path: str) -> None:
    st = sftp.stat(remote_path)
    if stat.S_ISDIR(st.st_mode):
        for name in sftp.listdir(remote_path):
            child = str(PurePosixPath(remote_path) / name)
            delete_remote_recursive(sftp, child)
        sftp.rmdir(remote_path)
    else:
        sftp.remove(remote_path)


def cmd_upload(args: argparse.Namespace, sftp: paramiko.SFTPClient) -> None:
    local = Path(args.local)
    if not local.exists():
        die(f"Local path does not exist: {local}")

    remote = normalize_remote(args.remote_root, args.remote)
    if local.is_dir():
        if not args.recursive:
            die(f"Local source is a directory, use --recursive: {local}")
        upload_dir_recursive(sftp, local, remote)
    else:
        upload_file(sftp, local, remote)

    print(json.dumps({"status": "uploaded", "local": str(local), "remote": remote}, ensure_ascii=False, indent=2))


def cmd_upload_ftp(args: argparse.Namespace, ftp: ftplib.FTP) -> None:
    local = Path(args.local)
    if not local.exists():
        die(f"Local path does not exist: {local}")

    remote = normalize_remote(args.remote_root, args.remote)
    if local.is_dir():
        if not args.recursive:
            die(f"Local source is a directory, use --recursive: {local}")
        ftp_upload_dir_recursive(ftp, local, remote)
    else:
        ftp_upload_file(ftp, local, remote)

    print(json.dumps({"status": "uploaded", "local": str(local), "remote": remote}, ensure_ascii=False, indent=2))


def cmd_download(args: argparse.Namespace, sftp: paramiko.SFTPClient) -> None:
    remote = normalize_remote(args.remote_root, args.remote)
    local = Path(args.local)

    st = sftp.stat(remote)
    if stat.S_ISDIR(st.st_mode):
        if not args.recursive:
            die(f"Remote source is a directory, use --recursive: {remote}")
        download_dir_recursive(sftp, remote, local)
    else:
        download_file(sftp, remote, local)

    print(json.dumps({"status": "downloaded", "remote": remote, "local": str(local)}, ensure_ascii=False, indent=2))


def cmd_download_ftp(args: argparse.Namespace, ftp: ftplib.FTP) -> None:
    remote = normalize_remote(args.remote_root, args.remote)
    local = Path(args.local)

    if not ftp_exists(ftp, remote):
        die(f"Remote path not found: {remote}")

    if ftp_is_dir(ftp, remote):
        if not args.recursive:
            die(f"Remote source is a directory, use --recursive: {remote}")
        ftp_download_dir_recursive(ftp, remote, local)
    else:
        ftp_download_file(ftp, remote, local)

    print(json.dumps({"status": "downloaded", "remote": remote, "local": str(local)}, ensure_ascii=False, indent=2))


def cmd_delete(args: argparse.Namespace, sftp: paramiko.SFTPClient) -> None:
    remote = normalize_remote(args.remote_root, args.remote)
    st = sftp.stat(remote)
    if stat.S_ISDIR(st.st_mode) and not args.recursive:
        die(f"Remote target is a directory, use --recursive: {remote}")

    delete_remote_recursive(sftp, remote)
    print(json.dumps({"status": "deleted", "remote": remote}, ensure_ascii=False, indent=2))


def cmd_delete_ftp(args: argparse.Namespace, ftp: ftplib.FTP) -> None:
    remote = normalize_remote(args.remote_root, args.remote)
    if not ftp_exists(ftp, remote):
        die(f"Remote path not found: {remote}")

    if ftp_is_dir(ftp, remote) and not args.recursive:
        die(f"Remote target is a directory, use --recursive: {remote}")

    ftp_delete_recursive(ftp, remote)
    print(json.dumps({"status": "deleted", "remote": remote}, ensure_ascii=False, indent=2))


def cmd_list(args: argparse.Namespace, sftp: paramiko.SFTPClient) -> None:
    remote = normalize_remote(args.remote_root, args.remote)
    st = sftp.stat(remote)
    if not stat.S_ISDIR(st.st_mode):
        die(f"Remote path is not a directory: {remote}")

    items = []
    for item in sorted(sftp.listdir_attr(remote), key=lambda x: x.filename.lower()):
        items.append(
            {
                "name": item.filename,
                "type": "dir" if stat.S_ISDIR(item.st_mode) else "file",
                "size": None if stat.S_ISDIR(item.st_mode) else item.st_size,
            }
        )

    print(json.dumps({"status": "ok", "remote": remote, "items": items}, ensure_ascii=False, indent=2))


def cmd_list_ftp(args: argparse.Namespace, ftp: ftplib.FTP) -> None:
    remote = normalize_remote(args.remote_root, args.remote)
    if not ftp_exists(ftp, remote):
        die(f"Remote path not found: {remote}")
    if not ftp_is_dir(ftp, remote):
        die(f"Remote path is not a directory: {remote}")

    items = ftp_list_items(ftp, remote)
    print(json.dumps({"status": "ok", "remote": remote, "items": items}, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage NAS files over SFTP/FTP/FTPS")
    parser.add_argument("--protocol", choices=["sftp", "ftp", "ftps"], help="Transfer protocol")
    parser.add_argument("--host", help="Server host, or endpoint like sftp://host:22 / ftps://host:21")
    parser.add_argument("--port", type=int, help="Server port (default: sftp=22, ftp/ftps=21)")
    parser.add_argument("--user", help="Login username")
    parser.add_argument("--password", help="Login password")
    parser.add_argument("--key-file", help="SSH private key path (SFTP only)")
    parser.add_argument("--key-passphrase", help="SSH key passphrase (SFTP only)")
    parser.add_argument(
        "--remote-root",
        default=os.getenv("REMOTE_ROOT") or os.getenv("SFTP_REMOTE_ROOT") or os.getenv("FTP_REMOTE_ROOT") or "/",
        help="Default remote root for relative remote paths",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_upload = sub.add_parser("upload", help="Upload file/folder to remote server")
    p_upload.add_argument("--local", required=True, help="Local source path")
    p_upload.add_argument("--remote", required=True, help="Remote destination path")
    p_upload.add_argument("--recursive", action="store_true", help="Required for directory upload")

    p_download = sub.add_parser("download", help="Download file/folder from remote server")
    p_download.add_argument("--remote", required=True, help="Remote source path")
    p_download.add_argument("--local", required=True, help="Local destination path")
    p_download.add_argument("--recursive", action="store_true", help="Required for directory download")

    p_delete = sub.add_parser("delete", help="Delete file/folder from remote server")
    p_delete.add_argument("--remote", required=True, help="Remote path")
    p_delete.add_argument("--recursive", action="store_true", help="Required for directory delete")

    p_list = sub.add_parser("list", help="List a remote directory")
    p_list.add_argument("--remote", default=".", help="Remote directory path")

    return parser


def main() -> None:
    load_environment()
    parser = build_parser()
    args = parser.parse_args()

    protocol, client, remote_client = connect(args)
    try:
        if args.command == "upload":
            if protocol == "sftp":
                cmd_upload(args, remote_client)
            else:
                cmd_upload_ftp(args, remote_client)
        elif args.command == "download":
            if protocol == "sftp":
                cmd_download(args, remote_client)
            else:
                cmd_download_ftp(args, remote_client)
        elif args.command == "delete":
            if protocol == "sftp":
                cmd_delete(args, remote_client)
            else:
                cmd_delete_ftp(args, remote_client)
        elif args.command == "list":
            if protocol == "sftp":
                cmd_list(args, remote_client)
            else:
                cmd_list_ftp(args, remote_client)
        else:
            die(f"Unsupported command: {args.command}")
    except FileNotFoundError as exc:
        die(f"Remote path not found: {exc}")
    except PermissionError as exc:
        die(f"Permission denied: {exc}")
    except OSError as exc:
        die(f"Filesystem operation failed: {exc}")
    except ftplib.all_errors as exc:
        die(f"FTP operation failed: {exc}")
    finally:
        try:
            remote_client.close()
        finally:
            try:
                client.close()
            except Exception:  # noqa: BLE001
                pass


if __name__ == "__main__":
    main()
