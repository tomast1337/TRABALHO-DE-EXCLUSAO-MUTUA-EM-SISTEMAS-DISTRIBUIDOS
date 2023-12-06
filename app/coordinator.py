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
        self.access_lock = threading.Lock()

    def add_to_queue(self, process_id):
        self.queue.put(process_id)

    def get_from_queue(self):
        if not self.queue.empty():
            return self.queue.get()

    def release_from_queue(self, process_id):
        if not self.queue.empty():
            if self.queue.get() == process_id:
                self._logger.info(f"Process {process_id} released the lock")
                self.access_lock.release()
            else:
                self._logger.error(f"Process {process_id} is not at the front of the queue")
        else:
            self._logger.error(f"Queue is empty")

    def queue_rep(self) ->str:
        if not self.queue.empty():
            return str(list(self.queue.queue))
        else:
            return "Queue is empty"
        
    def is_locked(self):
        return self.access_lock.locked()
    
    def acquire_lock(self):
        self.access_lock.acquire()

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
            try:
                while True:
                    conn, addr = s.accept()
                    self._logger.info(f"Process {addr} connected")
                    self.process_sockets[addr] = conn
                    # Criar uma thread para cada conexão
                    threading.Thread(target=self.handle_client, args=(conn, addr)).start()
            finally:
                self.close_server()
    
    def close_server(self):
        for addr in self.process_sockets.keys():
            self.process_sockets[addr].close()
        self._logger.info("Closing server")
        exit(0)

    def handle_client(self, conn, addr):
        while True: 
            data = conn.recv(1024)
            if not data:
                break
            data = data.decode()
            msg = Message.from_string(data)
            self.process_sockets_ids[addr] = msg.processID
            self.coordinator.receive_message(data,addr)
        self._logger.info(f"Process {addr} disconnected")
    
    def send_message(self, addr, message):
        self.process_sockets[addr].sendall(message.encode())

class Coordinator:
    def __init__(self, server_address=('localhost',12345)):
        self._logger = logging.getLogger(__name__)
        self.server_address = server_address
        self.queue_manager = QueueManager()
        self.process_counts = {}

    def start_server(self):
        self.socket_manager = SocketManager(self, self.server_address)
        self.socket_manager.start_server(self.socket_manager.accept_connections)
        
        algorithm_thread = threading.Thread(target=self.execute_coordinator)
        algorithm_thread.start()
        
        terminal_thread = threading.Thread(target=self.handle_terminal)
        terminal_thread.start()

    def execute_coordinator(self):
        while True:
            process_id = self.queue_manager.get_from_queue()
            addr = None
            addr = self.get_addr_from_process_id(process_id)
            if process_id is not None and addr is not None and not self.queue_manager.is_locked():
                self._logger.info(f"Process {process_id} is executing")
                self.queue_manager.acquire_lock()
                self.grant_access(process_id,addr)
                time.sleep(1)
            else:
                time.sleep(1) 

    def get_addr_from_process_id(self, process_id):
        addr = None
        for key in self.socket_manager.process_sockets_ids.keys():
            if self.socket_manager.process_sockets_ids[key] == process_id:
                addr = key
                break
        return addr 

    def close_server(self):
        self._logger.info("Exiting...")
        self.socket_manager.close_server()
        exit(0)

    def handle_terminal(self):
        while True:
            command = input()
            if command == "list":
                self._logger.info(f"Current queue: {self.queue_manager.queue_rep()}")
            if command == "listc": # list connected processes
                self._logger.info(f"Connected processes: {self.socket_manager.process_sockets}")
            elif command == "count":
                self._logger.info(f"Process counts: {self.process_counts}")
            elif command == "exit":
                self.close_server()
            else:
                self._logger.info(f"""
                                  
                                  \tInvalid command: {command}
                                  \tValid commands are:
                                  \tlist: prints the current queue
                                  \tcount: prints how many times each process was granted access
                                  \texit: exits the program

                                  """
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
            self.queue_manager.release_from_queue(msg.processID)
        else:
            self._logger.error(f"Invalid message type received: {msg.messageType}")

      