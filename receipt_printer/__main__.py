import logging
from receipt_printer import ReceiptPrinter

logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s [%(threadName)s]',
)

if __name__ == "__main__":
    x = ReceiptPrinter()
    x.start()
    try:
        input("Press enter key to end")
    except KeyboardInterrupt:
        pass
    x.terminate()
    x.join()
