from datetime import datetime
import time
from message import Message, MessageTypes
from process import Process
import logging
import queue
import threading
import socket

class QueueManager:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.queue = queue.Queue()


    def add_to_queue(self, process_id):
        self.queue.put(process_id)


    def get_from_queue(self):
        if not self.queue.empty():
            return self.queue.get()

class SocketManager:
    def __init__(self,coordinator, server_address=('localhost',12345)):
        self._logger = logging.getLogger(__name__)
        self.server_address = server_address
        self.process_sockets = {}
        self.process_sockets_ids = {}
        self.coordinator = coordinator

    def start_server(self, accept_connections):
        server_thread = threading.Thread(target=accept_connections)
        server_thread.start()

    def accept_connections(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(self.server_address)
            s.listen()
            while True:
                conn, addr = s.accept()
                self._logger.info(f"Process {addr} connected")
                self.process_sockets[addr] = conn
                threading.Thread(target=self.handle_client, args=(conn, addr)).start()
    
    def handle_client(self, conn, addr):
        while True: 
            data = conn.recv(1024)
            if not data:
                break
            data = data.decode()
            msg = Message.from_string(data)
            self.process_sockets_ids[addr] = msg.processID
            self.coordinator.receive_message(data,addr)
    
    def send_message(self, addr, message):
        self.process_sockets[addr].sendall(message.encode())

class Coordinator:
    def __init__(self, server_address=('localhost',12345)):
        self._logger = logging.getLogger(__name__)
        self.access_lock = threading.Lock()
        self.server_address = server_address
        self.queue_manager = QueueManager()
        self.process_counts = {}

    def start_server(self):
        self.socket_manager = SocketManager(self, self.server_address)


        self.socket_manager.start_server(self.socket_manager.accept_connections)
        
        algorithm_thread = threading.Thread(target=self.execute_algorithm)
        algorithm_thread.start()
        
        terminal_thread = threading.Thread(target=self.handle_terminal)
        terminal_thread.start()

    def execute_algorithm(self):
        while True:
            process_id = self.queue_manager.get_from_queue()
            addr = None
            for key in self.socket_manager.process_sockets_ids.keys():
                if self.socket_manager.process_sockets_ids[key] == process_id:
                    addr = key
                    break
            if process_id is not None and addr is not None:
                if not self.access_lock.locked():  # check if the lock is available
                    with self.access_lock:
                        self.grant_access(process_id,addr)
                else:
                    self._logger.info(f"Process {process_id} is waiting")
            else:
                time.sleep(1)  


    def handle_terminal(self):
        while True:
            command = input()
            if command == "list":
                self._logger.info(f"Current queue: {self.queue_manager.queue.queue}")
            if command == "listc": # list connected processes
                self._logger.info(f"Connected processes: {self.socket_manager.process_sockets.keys()}")
            elif command == "count":
                self._logger.info(f"Process counts: {self.process_counts}")
            elif command == "exit":
                exit(0)
            else:
                self._logger.info("""Invalid command !
                                  \tValid commands are:
                                  \tlist: prints the current queue
                                  \tcount: prints how many times each process was granted access
                                  \texit: exits the program"""
                                  )
        

    def grant_access(self, process_id,addr):
        msg = Message('1', process_id, MessageTypes.GRANT)
        self.socket_manager.send_message(addr, msg.create_message())
       
    def receive_message(self, message:str,addr:tuple):
        msg = Message.from_string(message)
        self._logger.info(f"Received {msg.messageType} from Process {msg.processID} at {datetime.now()} ")
        if msg.messageType == MessageTypes.REQUEST:
            self.queue_manager.add_to_queue(msg.processID)
        elif msg.messageType == MessageTypes.RELEASE:
            self.process_counts[msg.processID] = self.process_counts.get(msg.processID, 0) + 1 + 1
            if self.access_lock.locked():
                self.access_lock.release()
        else:
            self._logger.error(f"Invalid message type received: {msg.messageType}")

      