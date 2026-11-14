"""Assignment 6: Simple TCP service banner grabber.
Use only on systems you own or are allowed to test.
"""

import argparse
import socket
import ssl

HTTP_PORTS = {80, 8000, 8080, 8888}
HTTPS_PORTS = {443, 8443}


def parse_ports(value):
    """Convert a comma-separated port list to unique valid port numbers."""
    ports = []
    for item in value.split(","):
        item = item.strip()
        if not item.isdigit():
            raise ValueError("Enter port numbers separated by commas, e.g. 21,22,80")
        port = int(item)
        if not 1 <= port <= 65535:
            raise ValueError("Port numbers must be between 1 and 65535")
        if port not in ports:
            ports.append(port)
    if not ports or len(ports) > 32:
        raise ValueError("Select between 1 and 32 ports")
    return ports


def get_text(data):
    """Get the first printable line of the service response."""
    text = data.decode("utf-8", errors="ignore")
    lines = text.splitlines()
    first_line = lines[0].strip() if lines else ""
    server = ""
    for line in lines[1:]:
        if line.lower().startswith("server:"):
            server = line.split(":", 1)[1].strip()
            break
    return first_line, server


def receive_banner(connection, http=False):
    """Read at most 1024 bytes; HTTP headers may arrive in several chunks."""
    data = b""
    while len(data) < 1024:
        try:
            part = connection.recv(1024 - len(data))
        except socket.timeout:
            break
        if not part:
            break
        data += part
        if (not http and b"\n" in data) or (http and (b"\r\n\r\n" in data or b"\n\n" in data)):
            break
    return data


def scan_port(host, port, timeout=2.0, mode="auto"):
    """Return (status, first_line, server) for one TCP port."""
    use_http = mode == "http" or (mode == "auto" and port in HTTP_PORTS)
    use_https = mode == "https" or (mode == "auto" and port in HTTPS_PORTS)

    try:
        with socket.create_connection((host, port), timeout=timeout) as raw_socket:
            raw_socket.settimeout(timeout)
            connection = raw_socket
            if use_https:
                context = ssl.create_default_context()
                connection = context.wrap_socket(raw_socket, server_hostname=host)
                connection.settimeout(timeout)

            try:
                return _read_service(connection, host, use_http or use_https)
            finally:
                if connection is not raw_socket:
                    connection.close()
    except (socket.timeout, TimeoutError):
        return "TIMEOUT", "Connection timed out", ""
    except ConnectionRefusedError:
        return "CLOSED", "Connection refused", ""
    except (socket.gaierror, OSError, ssl.SSLError) as error:
        return "ERROR", str(error), ""


def _read_service(connection, host, send_http_request):
    """Ask HTTP services for headers, otherwise wait for the greeting."""
    try:
        if send_http_request:
            request = (
                    "HEAD / HTTP/1.1\r\n"
                    f"Host: {host}\r\n"
                    "Connection: close\r\n\r\n"
                )
            connection.sendall(request.encode("ascii", errors="ignore"))

        data = receive_banner(connection, http=send_http_request)
        first_line, server = get_text(data)
        return "OPEN", first_line or "No banner received", server
    except (ConnectionResetError, BrokenPipeError):
        return "OPEN", "Connection closed without a banner", ""


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Banner Grabber - Assignment 6 (authorized hosts only)"
    )
    parser.add_argument("host", help="IP address or hostname")
    parser.add_argument(
        "ports", nargs="?", default="21,22,80,443",
        help="Comma-separated ports (default: 21,22,80,443)",
    )
    parser.add_argument(
        "--timeout", type=float, default=2.0, help="Timeout in seconds (default: 2)"
    )
    parser.add_argument(
        "--mode", choices=("auto", "passive", "http", "https"),
        default="auto", help="Protocol mode (default: auto)",
    )
    options = parser.parse_args(args)
    try:
        ports = parse_ports(options.ports)
    except ValueError as error:
        parser.error(str(error))
    if not 0.1 <= options.timeout <= 30:
        parser.error("Timeout must be between 0.1 and 30 seconds")

    print("=== Assignment 6: Banner Grabbing Tool ===")
    print("Target:", options.host)
    print("Ports:", ", ".join(str(p) for p in ports))
    print("-" * 48)
    for port in ports:
        status, banner, server = scan_port(
            options.host, port, timeout=options.timeout, mode=options.mode
        )
        print(f"Port {port}: {status}")
        if status == "OPEN":
            print("  Banner:", banner)
            if server:
                print("  Server:", server)
        else:
            print("  Info:", banner)
    print("-" * 48)
    print("Scan completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
