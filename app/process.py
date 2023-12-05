import threading
import time
import logging
from message import Message , MessageTypes
import socket
import time
from datetime import datetime

class Process(threading.Thread):
    def __init__(self, processID, coordinator_address, filename = "processes.txt"):
        threading.Thread.__init__(self)
        self.processID = processID
        self.coordinator_address = coordinator_address
        self.filename = filename

        self._logger = logging.getLogger(__name__)

    def run(self):
        self.request_access()
        time.sleep(5) # simulate work for 5 seconds
        self.release_access()

    def request_access(self):
        msg = Message(str(self.processID), str(self.processID), MessageTypes.REQUEST)
        self.send_message(msg.create_message())

    def release_access(self):
        msg = Message(str(self.processID), str(self.processID), MessageTypes.RELEASE)
        self.send_message(msg.create_message())

    def send_message(self, message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(self.coordinator_address)
            s.sendall(message.encode())
            self._logger.info(f"Process {self.processID} sent: {message}")
            self.write_to_file(message)

    def write_to_file(self, message):
        with open(self.filename, "a") as file:
            formatted_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            file.write(f"Process {self.processID} sent: {message} at {formatted_time }\n")