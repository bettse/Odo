import logging
from ibeacon import IBeacon

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s [%(threadName)s]',
)

if __name__ == "__main__":
    x = IBeacon()
    x.start()
    try:
        input("Press enter key to end\n")
    except KeyboardInterrupt:
        pass
    x.terminate()
    x.join()
