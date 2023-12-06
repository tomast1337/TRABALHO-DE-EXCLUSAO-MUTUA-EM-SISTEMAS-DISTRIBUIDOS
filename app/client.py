import logging
from rich.logging import RichHandler
from process import Process
import Pyro4

format="%(asctime)s (%(threadName)-2s) %(message)s"
logging.basicConfig(
    level=logging.NOTSET,
    format=format,
    datefmt="[%X]",
    handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)

id = int(input("Enter process id: "))

if id > 9 or id < 0:
    logger.error("Invalid process id. Process id must be between 0 and 9")
    exit()

uri = input("Enter the uri of the coordinator: ").strip()

if uri == "":
    logger.error("Invalid uri")
    exit()


process = Process(
        process_id = str(id),
        coordinator = Pyro4.Proxy(uri),
        filename="processes.log"
)
logger.info(f"Process {id} starting...")
process.start()
process.join()
logger.info("Processes closed")