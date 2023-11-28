import socket
from rich.logging import RichHandler

format="%(asctime)s (%(threadName)-2s) %(message)s"
logging.basicConfig(
    level="NOTSET", format=format, datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)

class Client:
    def __init__(self, host='localhost', port=12345):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (host, port)
        self.sock.connect(self.server_address)

        self._logger = logging.getLogger(__name__)

    def send_message(self, message):
        try:
            self.sock.sendall(message.encode())
            self._logger.info(f"Sent: {message}")
        except Exception as e:
            self._logger.error(f"Error: {e}")
        finally:
            self._logger.info("Closing socket")
            self.sock.close()

logger.info("Starting client")

client = Client()
logger.info("Sending message")
client.send_message("1|1|REQUEST")
client = Client()
client.send_message("1|1|RELEASE")