import logging
import random
from threading import Thread
import time
import Pyro4
from rich.logging import RichHandler
from process import Process

format="%(asctime)s (%(threadName)-2s) %(message)s"
logging.basicConfig(
    level=logging.DEBUG,
    format=format,
    datefmt="[%X]",
    handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)

quantity = int(input("Enter the quantity of processes: "))

if quantity > 9 or quantity < 0:
    logger.error("Invalid quantity. Quantity must be between 0 and 9")
    exit()


uri = input("Enter the uri of the coordinator: ").strip()

if uri == "":
    logger.error("Invalid uri")
    exit()


def main_processs():
    # create a process for each process id
    processes = []
    indices = [str(i) for i in range(quantity)]
    random.shuffle(indices)
    for i in indices:
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
    Thread(target=main_processs).start()