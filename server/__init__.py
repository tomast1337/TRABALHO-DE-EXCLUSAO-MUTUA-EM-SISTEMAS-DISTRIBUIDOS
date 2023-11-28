import threading
import socket
import time
import queue
import logging
from rich.logging import RichHandler

format="%(asctime)s (%(threadName)-2s) %(message)s"
logging.basicConfig(
    level="NOTSET", format=format, datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)

class Message:
    
    def __init__(self, messageID, processID, messageType):
        self.messageID = messageID
        self.processID = processID
        self.messageType = messageType
        
        self._logger = logging.getLogger(__name__)

    def create_message(self):
        return f"{self.messageID}|{self.processID}|{self.messageType}"

    def parse_message(self, message):
        parts = message.split("|")
        self.messageID = parts[0]
        self.processID = parts[1]
        self.messageType = parts[2]

class Process(threading.Thread):
    def __init__(self, processID, coordinator):
        threading.Thread.__init__(self)
        self.processID = processID
        self.coordinator = coordinator

        self._logger = logging.getLogger(__name__)

    def run(self):
        self.request_access()
        self.write_to_file()
        self.release_access()

    def request_access(self):
        msg = Message(self.processID, self.processID, "REQUEST")
        self.coordinator.queue.put(msg.create_message())

    def write_to_file(self):
        with open("resultado.txt", "a") as file:
            file.write(f"Process {self.processID} accessed at {time.time()}\n")

    def release_access(self):
        msg = Message(self.processID, self.processID, "RELEASE")
        self.coordinator.queue.put(msg.create_message())

class Coordinator:
    def __init__(self):
        self.queue = queue.Queue()
        self.processes = []

        self._logger = logging.getLogger(__name__)

    def accept_connection(self, process):
        self.processes.append(process)

    def grant_access(self):
        while True:
            if not self.queue.empty():
                msg = Message(0, 0, "")
                msg.parse_message(self.queue.get())
                if msg.messageType == "REQUEST":
                    print(f"Process {msg.processID} granted access")
                elif msg.messageType == "RELEASE":
                    print(f"Process {msg.processID} released access")

coordinator = Coordinator()
for i in range(5):
    process = Process(i, coordinator)
    coordinator.accept_connection(process)
    process.start()

coordinator.grant_access()