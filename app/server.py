import logging
import Pyro4
from rich.logging import RichHandler
from coordinator import Coordinator

format="%(asctime)s (%(threadName)-2s) %(message)s"
logging.basicConfig(
    level="NOTSET", format=format, datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)



def main():
    daemon = Pyro4.Daemon()
    logger.info("Coordinator starting...")
    uri = daemon.register(Coordinator)
    logger.info(f"Coordinator uri: {uri}")
    daemon.requestLoop()

if __name__=="__main__":
    main()
