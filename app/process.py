import threading
import time
import logging
from message import Message , MessageTypes
import time
from datetime import datetime
import Pyro4
import random

class Process(threading.Thread):
    def __init__(self, 
                 process_id:str,
                    coordinator:Pyro4.Proxy,
                    filename:str
                    ):
        threading.Thread.__init__(self)
        self.process_id = process_id
        self.coordinator = coordinator
        self.filename = filename
        self._logger = logging.getLogger(__name__)

    def run(self):
        while True:
            try:
                self.work()
                time.sleep(1)
            except KeyboardInterrupt:
                self._logger.info(f"Process {self.process_id} interrupted")
                break

        
    def work(self):
        # Request access message
        self.write_to_file(MessageTypes.REQUEST)
        message = Message(
                messageID = "1",
                processID = self.process_id,
                messageType = MessageTypes.REQUEST
        ).create_message()

        # wait for GRANT message
        response = None
        while True:
            response = self.coordinator.handle_message(message)
            if response is None:
                self._logger.info(f"Process {self.process_id} waiting for access")
                time.sleep(1)
            else:
                break

        # write to file when access is granted
        self.write_to_file(MessageTypes.GRANT)
        
        time.sleep(random.randint(3,5)) # simulate work in the critical section
            
        # Release access message
        self.write_to_file(MessageTypes.RELEASE)
        message = Message(
                messageID = "1",
                processID = self.process_id,
                messageType = MessageTypes.RELEASE
        ).create_message()
        self.coordinator.handle_message(message)

        time.sleep(random.randint(3,5)) # simulate work outside the critical section

    def write_to_file(self, message=""):
        with open(self.filename, 'a') as f:
            f.write(f"Process {self.process_id} wrote to file at {datetime.now()}, {message}\n")
        self._logger.info(f"Process {self.process_id} wrote to file at {datetime.now()}")
