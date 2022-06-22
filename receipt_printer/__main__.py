import yaml
import logging
from receipt_printer import ReceiptPrinter

logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s [%(threadName)s]',
)

if __name__ == "__main__":
    try:
        with open('config.yaml','r') as file:
            config = yaml.safe_load(file)
    except IOError:
        logger.error("No config file, see config.yaml.sample")
        sys.exit(1)
    modules = config['modules']

    x = ReceiptPrinter(**modules['receipt_printer'])
    x.start()
    try:
        input("Press enter key to end\n")
    except KeyboardInterrupt:
        pass
    x.terminate()
    x.join()
