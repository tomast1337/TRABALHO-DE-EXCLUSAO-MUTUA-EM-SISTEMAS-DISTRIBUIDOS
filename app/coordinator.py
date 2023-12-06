from typing import Union
from message import Message, MessageTypes
import logging
import queue
import threading
import Pyro4

@Pyro4.expose
@Pyro4.behavior(instance_mode="single") # singleton
class Coordinator(object):
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.queue = queue.Queue()
        self.process_counts = {} # keeps track of how many times each process released the access
        self.access_lock = threading.Lock()  # add a lock to the queue

        self.terminal_thread = threading.Thread(target=self.handle_terminal)
        self.terminal_thread.start()

    def handle_terminal(self):
        while True:
            command = input()
            if command == "list":
                self._logger.debug(f"Current queue: {self.queue_manager.queue_rep()}")
            if command == "listc": # list connected processes
                self._logger.debug(f"Connected processes: {self.socket_manager.process_sockets}")
            elif command == "count":
                self._logger.debug(f"Process counts: {self.process_counts}")
            elif command == "exit":
                self.close_server()
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
            self._logger.error(e.with_traceback())
            raise Exception(e)


    def _request_access(self,message:Message) -> Union[str,None]:
        # Check if the queue is locked
        if self.access_lock.locked():
            self._logger.debug(f"Queue is locked, cannot add Process {message.processID}")
            return None

        # Check if the process is already in the queue
        if message.processID in list(self.queue.queue):
            self._logger.debug(f"Process {message.processID} is already in the queue")
            return None
        
        # Add the process ID to the queue
        self.queue.put(message.processID)
        self._logger.debug(f"Process {message.processID} added to queue")

        # Check if the process is the first in the queue
        if self.queue.queue[0] == message.processID:
            self.access_lock.acquire()  # lock the queue
            self._logger.debug(f"Process {message.processID} locked the queue and acquired access")
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
            self.process_counts[message.processID] = self.process_counts.get(message.processID, 0) + 1
            # Unlock the queue
            self.access_lock.release()
            self._logger.debug(f"Process {message.processID} removed from queue and unlocked")
            return None
        else:
            raise Exception(f"Process {message.processID} is not at the front of the queue")

      