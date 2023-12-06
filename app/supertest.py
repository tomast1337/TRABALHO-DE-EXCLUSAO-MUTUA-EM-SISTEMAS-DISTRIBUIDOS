import logging
import Pyro4
from rich.logging import RichHandler
from coordinator import Coordinator
from process import Process

format="%(asctime)s (%(threadName)-2s) %(message)s"
logging.basicConfig(
    level=logging.NOTSET,
    format=format,
    datefmt="[%X]",
    handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)

quantity = int(input("Enter the quantity of processes: "))

if quantity > 9 or quantity < 0:
    logger.error("Invalid quantity. Quantity must be between 0 and 9")
    exit()

def main():
    daemon = Pyro4.Daemon()
    logger.info("Coordinator starting...")
    uri = daemon.register(Coordinator)
    logger.info(f"Coordinator uri: {uri}")
    daemon.requestLoop()

    # create a process for each process id
    processes = []
    for i in range(quantity):
        process = Process(
            process_id = str(i),
            coordinator = Pyro4.Proxy(uri),
            filename="processes.log"
        )
        processes.append(process)
        process.start()

    # wait for all processes to finish
    for process in processes:
        process.join()

    logger.info("Processes closed")

if __name__=="__main__":
    main()