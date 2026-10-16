"""Exercise a queued stop packet preceding a command acknowledgement."""
import socket
import threading
import unittest

from mgba_headless_gdb_capture import GdbRemote


class TransportTest(unittest.TestCase):
    def test_queued_stop_after_ack(self):
        client, server = socket.socketpair()
        errors = []
        def peer():
            try:
                server.settimeout(2)
                self.assertEqual(server.recv(1024), GdbRemote._packet(b"m8485030,4"))
                server.sendall(b"+" + GdbRemote._packet(b"T05"))
                self.assertEqual(server.recv(1), b"+")
                server.sendall(GdbRemote._packet(b"b4504808"))
                self.assertEqual(server.recv(1), b"+")
            except Exception as error:
                errors.append(error)
        worker = threading.Thread(target=peer)
        worker.start()
        try:
            remote = GdbRemote(client)
            self.assertEqual(remote.read_memory(0x08485030, 4), bytes.fromhex("b4504808"))
            self.assertEqual(remote.asynchronous_stops, ["T05"])
            worker.join(3)
            self.assertFalse(worker.is_alive())
            self.assertEqual(errors, [])
        finally:
            client.close()
            server.close()

    def test_queued_stop_before_ack(self):
        client, server = socket.socketpair()
        errors = []

        def peer():
            try:
                server.settimeout(2)
                self.assertEqual(server.recv(1024), GdbRemote._packet(b"g"))
                server.sendall(GdbRemote._packet(b"T05"))
                self.assertEqual(server.recv(1), b"+")
                server.sendall(b"+" + GdbRemote._packet(b"1234"))
                self.assertEqual(server.recv(1), b"+")
            except Exception as error:
                errors.append(error)

        worker = threading.Thread(target=peer)
        worker.start()
        try:
            remote = GdbRemote(client)
            self.assertEqual(remote.command("g"), b"1234")
            self.assertEqual(remote.asynchronous_stops, ["T05"])
            worker.join(3)
            self.assertFalse(worker.is_alive())
            self.assertEqual(errors, [])
        finally:
            client.close()
            server.close()


if __name__ == "__main__":
    unittest.main()
