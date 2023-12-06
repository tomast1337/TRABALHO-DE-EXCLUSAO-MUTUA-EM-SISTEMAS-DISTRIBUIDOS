import logging
from rich.logging import RichHandler
from coordinator import Coordinator
from process import Process

format="%(asctime)s (%(threadName)-2s) %(message)s"
logging.basicConfig(
    level="NOTSET", format=format, datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)

coordinator_host = ('localhost', 12345)
# Create 5 Process clients and connect them to the Coordinator

id = input("Enter process id: ")

process = Process(str(id), coordinator_host)
process.start()
logger.info(f"Process {id} started")
process.join()
logger.info("Processes closed")