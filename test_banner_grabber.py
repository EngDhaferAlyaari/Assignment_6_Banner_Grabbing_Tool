"""Local-only tests: no connection is made to an outside host."""

import contextlib
import io
import socket
import threading
import time
import unittest
from unittest.mock import patch

from banner_grabber import get_text, main, parse_ports, scan_port


class LocalService:
    def __init__(self, answer, is_http=False, delay=0.0, split_reply=False):
        self.answer = answer
        self.is_http = is_http
        self.delay = delay
        self.split_reply = split_reply
        self.server = None
        self.thread = None
        self.port = None
        self.request = b""

    def __enter__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("127.0.0.1", 0))
        self.server.listen(1)
        self.port = self.server.getsockname()[1]

        def worker():
            try:
                client, _ = self.server.accept()
                with client:
                    client.settimeout(1)
                    if self.is_http:
                        self.request = client.recv(1024)
                    if self.delay:
                        time.sleep(self.delay)
                    if self.answer:
                        if self.split_reply:
                            mid = max(1, len(self.answer) // 2)
                            client.sendall(self.answer[:mid])
                            time.sleep(0.02)
                            client.sendall(self.answer[mid:])
                        else:
                            client.sendall(self.answer)
            except (OSError, BrokenPipeError):
                pass

        self.thread = threading.Thread(target=worker, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.server.close()
        self.thread.join(timeout=1)


class BannerTests(unittest.TestCase):
    def test_ports_simple(self):
        self.assertEqual(parse_ports("21,22,80"), [21, 22, 80])

    def test_ports_duplicate(self):
        self.assertEqual(parse_ports("21, 21,80,21"), [21, 80])

    def test_ports_out_of_range(self):
        for bad in ("0", "65536", "-1", "abc", "21,a", "", ",21"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_ports(bad)

    def test_port_limit(self):
        with self.assertRaises(ValueError):
            parse_ports(",".join(map(str, range(1, 34))))

    def test_first_banner_line(self):
        self.assertEqual(get_text(b"SSH-2.0-OpenSSH_9.6\r\nextra\r\n")[0], "SSH-2.0-OpenSSH_9.6")

    def test_server_header(self):
        first, server = get_text(b"HTTP/1.1 200 OK\r\nServer: nginx/1.24\r\n\r\n")
        self.assertEqual((first, server), ("HTTP/1.1 200 OK", "nginx/1.24"))

    def test_invalid_utf8(self):
        self.assertEqual(get_text(b"220 FTP\xff Server\r\n")[0], "220 FTP Server")

    def test_empty_banner(self):
        self.assertEqual(get_text(b""), ("", ""))

    def test_ssh_mock(self):
        with LocalService(b"SSH-2.0-OpenSSH_9.6\r\n") as service:
            self.assertEqual(scan_port("127.0.0.1", service.port, 1, "passive"),
                             ("OPEN", "SSH-2.0-OpenSSH_9.6", ""))

    def test_ftp_mock(self):
        with LocalService(b"220 (vsFTPd 3.0.5)\r\n") as service:
            self.assertEqual(scan_port("127.0.0.1", service.port, 1, "passive")[1],
                             "220 (vsFTPd 3.0.5)")

    def test_http_mock(self):
        reply = b"HTTP/1.1 200 OK\r\nServer: Apache/2.4.62\r\nContent-Length: 0\r\n\r\n"
        with LocalService(reply, is_http=True) as service:
            result = scan_port("127.0.0.1", service.port, 1, "http")
            self.assertEqual(result, ("OPEN", "HTTP/1.1 200 OK", "Apache/2.4.62"))
            self.assertIn(b"HEAD / HTTP/1.1\r\n", service.request)

    def test_http_split_packets(self):
        reply = b"HTTP/1.1 200 OK\r\nServer: nginx/1.26\r\nConnection: close\r\n\r\n"
        with LocalService(reply, is_http=True, split_reply=True) as service:
            self.assertEqual(scan_port("127.0.0.1", service.port, 1, "http")[2], "nginx/1.26")

    def test_http_restricted_to_1024(self):
        reply = b"HTTP/1.1 200 OK\r\n" + b"X-Test: " + (b"A" * 1800) + b"\r\n\r\n"
        with LocalService(reply, is_http=True) as service:
            self.assertEqual(scan_port("127.0.0.1", service.port, 1, "http")[0], "OPEN")

    def test_open_no_banner(self):
        with LocalService(b"") as service:
            self.assertEqual(scan_port("127.0.0.1", service.port, 1, "passive"),
                             ("OPEN", "No banner received", ""))

    def test_closed_port(self):
        # A free local port may time out instead of refusing on some systems.
        # Simulate the refused connection to check the CLOSED status reliably.
        with patch("banner_grabber.socket.create_connection",
                   side_effect=ConnectionRefusedError("Connection refused")):
            self.assertEqual(scan_port("127.0.0.1", 65000, 0.3, "passive")[0],
                             "CLOSED")

    def test_receive_timeout_no_crash(self):
        with LocalService(b"Never sent", delay=0.3) as service:
            result = scan_port("127.0.0.1", service.port, 0.05, "passive")
            self.assertEqual(result, ("OPEN", "No banner received", ""))

    def test_connect_timeout_no_crash(self):
        with patch("banner_grabber.socket.create_connection", side_effect=socket.timeout):
            self.assertEqual(scan_port("127.0.0.1", 1234)[0], "TIMEOUT")

    def test_unresolvable_host(self):
        with patch("banner_grabber.socket.create_connection", side_effect=socket.gaierror("unknown")):
            self.assertEqual(scan_port("invalid.test", 80)[0], "ERROR")

    def test_main_prints_status(self):
        with LocalService(b"220 FTP ready\r\n") as service:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["127.0.0.1", str(service.port), "--mode", "passive"]), 0)
            self.assertIn("220 FTP ready", output.getvalue())
            self.assertIn("Scan completed.", output.getvalue())

    def test_main_invalid_timeout(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(["127.0.0.1", "21", "--timeout", "0"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
