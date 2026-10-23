"""Windows integration check using an isolated MySQL server and real browser.

Run with backend/.venv/Scripts/python.exe. It never connects to your MySQL service.
All processes are owned by this script and stopped in finally. Test data/logs remain
under ignored .local/. Uses installed MySQL binaries, Node and Microsoft Edge.
"""
import argparse
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time

import httpx
from PIL import Image
import pymysql

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"
HIDDEN = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_http(url, process):
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError(f"Service exited before readiness: {url}; see .local logs.")
        try:
            if httpx.get(url, timeout=1).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    raise RuntimeError(f"Service did not become ready: {url}; see .local logs.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mysql-bin", type=Path, default=Path(r"C:\Program Files\MySQL\MySQL Server 8.0\bin"))
    parser.add_argument("--skip-browser", action="store_true")
    args = parser.parse_args()
    mysql_exe = args.mysql_bin / "mysqld.exe"
    if not mysql_exe.is_file():
        raise SystemExit("MySQL server binary not found. Supply --mysql-bin with its directory.")
    LOCAL.mkdir(exist_ok=True)
    data_dir = Path(tempfile.mkdtemp(prefix="mysql-verification-", dir=LOCAL))
    mysql_port, api_port, ui_port = free_port(), free_port(), free_port()
    password = secrets.token_urlsafe(32)
    database = "foundation_test_" + secrets.token_hex(6)
    processes, logs = [], []
    mysql_process = None
    password_set = False

    def run(command, cwd=ROOT, env=None):
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", creationflags=HIDDEN)
        print(result.stdout, end="", flush=True)
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr, flush=True)
        result.check_returncode()

    def launch(command, name, cwd=ROOT, env=None):
        log = (LOCAL / f"{name}.log").open("w", encoding="utf-8")
        logs.append(log)
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=HIDDEN)
        processes.append(process)
        return process

    try:
        print("Initializing an isolated MySQL data directory under .local/.", flush=True)
        run([str(mysql_exe), "--no-defaults", "--initialize-insecure", f"--datadir={data_dir}",
             f"--basedir={args.mysql_bin.parent}"])
        mysql_process = launch([str(mysql_exe), "--no-defaults", f"--datadir={data_dir}",
                                f"--basedir={args.mysql_bin.parent}", "--bind-address=127.0.0.1",
                                f"--port={mysql_port}", "--mysqlx=OFF", "--skip-log-bin", "--console"], "mysql")
        connection = None
        for _ in range(100):
            if mysql_process.poll() is not None:
                raise RuntimeError("Isolated MySQL exited; see .local/mysql.log.")
            try:
                connection = pymysql.connect(host="127.0.0.1", port=mysql_port, user="root", connect_timeout=1)
                break
            except pymysql.Error:
                time.sleep(0.2)
        if connection is None:
            raise RuntimeError("Isolated MySQL did not become ready.")
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY %s", (password,))
                password_set = True
                # Identifier is generated above from a fixed prefix plus hex, not user input.
                cursor.execute(f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4")
        env = os.environ.copy()
        env.update({"MYSQL_HOST": "127.0.0.1", "MYSQL_PORT": str(mysql_port),
                    "MYSQL_DATABASE": database, "MYSQL_USER": "root", "MYSQL_PASSWORD": password,
                    "UPLOAD_DIR": str(data_dir / "uploads"), "MAX_UPLOAD_BYTES": "10485760",
                    "MAX_IMAGE_PIXELS": "25000000", "CORS_ORIGINS": f'["http://127.0.0.1:{ui_port}"]',
                    "FOUNDATION_TEST_MYSQL_PORT": str(mysql_port), "FOUNDATION_TEST_MYSQL_DATABASE": database,
                    "FOUNDATION_TEST_MYSQL_PASSWORD": password,
                    "VITE_API_BASE_URL": f"http://127.0.0.1:{api_port}",
                    "FOUNDATION_API_URL": f"http://127.0.0.1:{api_port}",
                    "FOUNDATION_UI_URL": f"http://127.0.0.1:{ui_port}"})
        run([sys.executable, "-m", "app.init_db"], ROOT / "backend", env)
        print("Running backend tests against real MySQL.", flush=True)
        # Use fresh workspace temp paths; sandbox and desktop users can have
        # different permissions on the OS's shared pytest temp/cache directories.
        run([sys.executable, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider",
             "--basetemp", str(data_dir / "pytest-temp")], ROOT / "backend", env)
        if not args.skip_browser:
            Image.new("RGB", (640, 480), color=(93, 112, 89)).save(LOCAL / "test-site.png")
            api = launch([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
                          "--port", str(api_port)], "api", ROOT / "backend", env)
            node = shutil.which("node")
            if node is None:
                raise RuntimeError("Node is not on PATH.")
            ui = launch([node, "node_modules/vite/bin/vite.js", "--host", "127.0.0.1", "--port", str(ui_port)],
                        "frontend", ROOT / "frontend", env)
            wait_http(env["FOUNDATION_API_URL"] + "/health/ready", api)
            wait_http(env["FOUNDATION_UI_URL"], ui)
            run([node, "node_modules/@playwright/test/cli.js", "test"], ROOT / "frontend", env)
            with pymysql.connect(host="127.0.0.1", port=mysql_port, user="root", password=password,
                                 database=database) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*), MIN(site_context) FROM site_uploads")
                    count, context = cursor.fetchone()
                    assert count == 1 and context == "Verification fixture only; not a real site assessment."
            print("Verified: browser -> FastAPI -> image file + MySQL -> persisted browser history.", flush=True)
        print("Foundation verification passed. Artifacts are in .local/.", flush=True)
    finally:
        for process in reversed(processes):
            if process is mysql_process or process.poll() is not None:
                continue
            process.terminate()
            process.wait(timeout=15)
        if mysql_process and mysql_process.poll() is None:
            try:
                with pymysql.connect(host="127.0.0.1", port=mysql_port, user="root",
                                     password=password if password_set else "", connect_timeout=2) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("SHUTDOWN")
                mysql_process.wait(timeout=15)
            except (pymysql.Error, subprocess.TimeoutExpired):
                mysql_process.terminate()
                mysql_process.wait(timeout=15)
        for log in logs:
            log.close()


if __name__ == "__main__":
    main()
