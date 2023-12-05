import unittest
from unittest.mock import patch
from message import Message, MessageTypes
from process import Process
import logging
import queue
import threading
import socket

class Coordinator:
    def __init__(self, host='localhost', port=12345):
        self.queue = queue.Queue()
        self.server_address = (host, port)

        self._logger = logging.getLogger(__name__)

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(self.server_address)
            s.listen()
            while True:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024)
                    if not data:
                        break
                    msg = Message('0', '0', MessageTypes.GRANT)
                    msg.parse_message(data.decode())
                    if msg.messageType == MessageTypes.REQUEST:
                        self._logger.info(f"Process {msg.processID} granted access")
                    elif msg.messageType == MessageTypes.RELEASE:
                        self._logger.info(f"Process {msg.processID} released access")

    def start(self):
        server_thread = threading.Thread(target=self.start_server)
        server_thread.start()