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

# Create 5 Process clients and connect them to the Coordinator
processes = []
for i in range(5):
    process = Process(str(i), coordinator_host)
    processes.append(process)
    process.start()
    logger.info(f"Process {i} started")

# Wait for the Processes to finish
for process in processes:
    process.join()

logger.info("Coordinator and Processes closed")