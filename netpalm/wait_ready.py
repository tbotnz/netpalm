"""Block until the local gunicorn process is accepting connections on port 9000."""

import socket
import sys
import time

HOST = "127.0.0.1"
PORT = 9000
TIMEOUT = 120
INTERVAL = 2


def main() -> None:
    deadline = time.monotonic() + TIMEOUT
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((HOST, PORT), timeout=2):
                print(f"netpalm API ready on {HOST}:{PORT}")
                return
        except OSError:
            time.sleep(INTERVAL)

    print(f"netpalm API not ready after {TIMEOUT}s", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
