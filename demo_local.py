"""Run a safe demonstration using three services on this computer only."""
import socket
import threading

from banner_grabber import scan_port


def start_mock_service(reply, is_http=False):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]

    def serve():
        try:
            connection, _ = listener.accept()
            with connection:
                connection.settimeout(2)
                if is_http:
                    connection.recv(1024)
                connection.sendall(reply)
        finally:
            listener.close()

    worker = threading.Thread(target=serve, daemon=True)
    worker.start()
    return port, worker


def main():
    services = [
        ("SSH (mock)", b"SSH-2.0-OpenSSH_9.6\r\n", "passive"),
        ("FTP (mock)", b"220 (vsFTPd 3.0.5)\r\n", "passive"),
        ("HTTP (mock)", b"HTTP/1.1 200 OK\r\nServer: Apache/2.4.62\r\n\r\n", "http"),
    ]
    print("Local demonstration only - 127.0.0.1")
    print("-" * 48)
    for name, response, mode in services:
        port, worker = start_mock_service(response, is_http=(mode == "http"))
        status, banner, server = scan_port("127.0.0.1", port, mode=mode)
        worker.join(timeout=2)
        print(f"{name} | Port {port}: {status}")
        print("  Banner:", banner)
        if server:
            print("  Server:", server)
    print("-" * 48)
    print("Demo completed.")


if __name__ == "__main__":
    main()
