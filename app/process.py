import threading
import time
import logging
from message import Message , MessageTypes
import socket
import time
from datetime import datetime

class Process(threading.Thread):
    def __init__(self, process_id, coordinator_address, filename="processes.txt"):
        threading.Thread.__init__(self)
        self.process_id = process_id
        self.coordinator_address = coordinator_address
        self.filename = filename
        self._logger = logging.getLogger(__name__)

    def work(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(self.coordinator_address)
        self._logger.info(f"Process {self.process_id} connected to coordinator")
        try:
            while True:  # repeat indefinitely
                request_msg = Message('1', self.process_id, MessageTypes.REQUEST).create_message()
                s.sendall(request_msg.encode())
                self._logger.info(f"Process {self.process_id} sent REQUEST message")
                self.write_to_file("REQUEST")
                while True:  # wait for GRANT message
                    data = s.recv(1024)
                    if not data:
                        continue
                    response_msg = Message.from_string(data.decode())
                    if response_msg.messageType == MessageTypes.GRANT:
                        self._logger.info(f"Process {self.process_id} received GRANT message")
                        self.write_to_file("GRANT")
                        time.sleep(5)  # wait for 2 seconds
                        release_msg = Message('2', self.process_id, MessageTypes.RELEASE).create_message()
                        self.write_to_file("RELEASE")
                        s.sendall(release_msg.encode())
                        self._logger.info(f"Process {self.process_id} sent RELEASE message")
                        break  # break the loop after receiving GRANT message
        except (BrokenPipeError, ConnectionResetError):
            self._logger.error(f"Process {self.process_id} was disconnected from coordinator")
        finally:
            s.close()
            
    def run(self):
        try:
            self.work()
        except Exception as e:
            self._logger.error(f"Process {self.process_id} error: {e}")
        except KeyboardInterrupt:
            self._logger.info(f"Process {self.process_id} interrupted")
        else:
            self._logger.info(f"Process {self.process_id} finished")

    def write_to_file(self, message=""):
        with open(self.filename, 'a') as f:
            f.write(f"Process {self.process_id} wrote to file at {datetime.now()}, {message}\n")
        self._logger.info(f"Process {self.process_id} wrote to file at {datetime.now()}")