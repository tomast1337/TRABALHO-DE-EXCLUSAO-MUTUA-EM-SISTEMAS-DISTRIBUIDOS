import logging
from rich.logging import RichHandler
from coordinator import Coordinator
from process import Process

format="%(asctime)s (%(threadName)-2s) %(message)s"
logging.basicConfig(
    level="NOTSET", format=format, datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)

# Create a Coordinator object
coordinator_host = ('localhost', 12345)
coordinator = Coordinator(coordinator_host)
logger.info("Coordinator created")

# Start the Coordinator server
coordinator.start_server()
logger.info("Coordinator server started")



