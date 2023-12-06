import time
from typing import Union
from message import Message, MessageTypes
import logging
import queue
import threading
import Pyro4

@Pyro4.expose
@Pyro4.behavior(instance_mode="single") # singleton
class Coordinator(object):
    def __init__(self, *args, **kwargs):
        self._logger = logging.getLogger(__name__)
        self.queue = queue.Queue()
        self.process_counts = {} # keeps track of how many times each process released the access
        self.access_lock = threading.Lock()  # add a lock to the queue
        self.lock_time = None
        self.timeout = 10 # seconds
        self.terminal_thread = threading.Thread(target=self.handle_terminal)
        self.terminal_thread.start()

    def handle_terminal(self):
        while True:
            command = input()
            if command == "list" or command == "l":
                if self.queue.empty():
                    self._logger.info("Queue is empty, locked: {self.access_lock.locked()}")
                else:
                    self._logger.info(f"Current queue: {list(self.queue.queue)}, locked: {self.access_lock.locked()}")
            elif command == "count" or command == "c":
                self._logger.info(f"Process counts: {self.process_counts}")
            elif command == "exit" or command == "e":
                self._logger.info("Exiting...")
                exit()
            else:
                self._logger.debug(f"""
                                  
                                  \tInvalid command: {command}
                                  \tValid commands are:
                                  \tlist: prints the current queue
                                  \tcount: prints how many times each process was granted access
                                  \texit: exits the program

                                  """
                                  )

    def handle_message(self,message:str) -> str:
        try:
            message_obj = Message.from_string(message)
            if message_obj.messageType == MessageTypes.REQUEST:
                return self._request_access(message_obj)
            elif message_obj.messageType == MessageTypes.RELEASE:
                return self._release_access(message_obj)
            else:
                self._logger.error(f"Invalid message type: {message_obj.messageType}")
                raise Exception(f"Invalid message type: {message_obj.messageType}")
        except Exception as e:
            self._logger.error(e)
            raise Exception(e)


    def _request_access(self,message:Message) -> Union[str,None]:
        # Check if the queue is locked
        if self.access_lock.locked():
            self._logger.debug(f"Queue is locked, cannot garant access Process {message.processID}")
            if self.lock_time is None:
                self.lock_time = time.time()
            elif time.time() - self.lock_time > self.timeout:
                current_process = self.queue.queue[0]
                self._logger.warn(f"{current_process} has been in the queue for more than {self.timeout} seconds, it will be removed from the queue, timeout for {message.processID}")
                self.queue.get()
                self.access_lock.release()
                self.lock_time = None

        # Check if the process is already in the queue
        if message.processID not in list(self.queue.queue):
            self.queue.put(message.processID)
            self._logger.debug(f"Process {message.processID} added to queue")
    
        # Check if the process is the first in the queue
        if self.queue.queue[0] == message.processID and not self.access_lock.locked():
            self.access_lock.acquire()  # lock the queue
            self._logger.debug(f"Process {message.processID} locked the queue and acquired access")
            self.lock_time = time.time() # set the lock time to now
            return Message(
                    messageID = "1",
                    processID = message.processID,
                    messageType = MessageTypes.GRANT
            ).create_message()
        else:
            return None

    
    def _release_access(self,message:Message) -> Union[str,None]:
        # Check if the process ID is at the front of the queue
        if not self.queue.empty() and self.queue.queue[0] == message.processID:
            # Remove the process ID from the queue
            self.queue.get()
            # Increment the count for the process
            self.process_counts[message.processID] = 1 + self.process_counts.get(message.processID, 0) # increment the count for the process, if it doesn't exist, set it to 0
            # Unlock the queue
            self.access_lock.release()
            self._logger.debug(f"Process {message.processID} removed from queue and unlocked")
            
            # clear the lock time
            self.lock_time = None
            return None
        else:
            raise Exception(f"Process {message.processID} is not at the front of the queue")

      