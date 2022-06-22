import pexpect
import sys
import json
import logging
import subprocess
from time import sleep
from datetime import datetime

from odo.models import BaseMqttDeviceModel
from espkey.models import ESPKeyCredential

logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s [%(threadName)s]',
)

class ReceiptPrinter(BaseMqttDeviceModel):
    def __init__(self, name='Star_Micronics___eb89b6a', options=[], *args, **kwargs):
        super(ReceiptPrinter, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger('odo.printer.Receipt')
        self.name = name
        self.options = options
        self._subscribe_topics = [
            self.credential_topic["seen"],
            self.command_topic
        ]

    def _on_message(self, client, userdata, msg):
        self.logger.debug(f"Message received-> {msg.topic} {str(msg.payload)}")

        if msg.topic in list(self.credential_topic.values()):
            self._handle_credential(msg=msg)

        if msg.topic == self.command_topic:
            self._handle_command(msg=msg)

    def _handle_credential(self, msg=None):
        message = json.loads(msg.payload)
        self.logger.debug(f"Handle Credential -> {message.get('type')}")

        if message["type"] == "wiegand":
            credential = ESPKeyCredential(payload=message["payload"])
            command = ['/usr/bin/lp', '-d', self.name]
            print(self.options)
            for option in self.options:
                command.append('-o')
                command.append(option)

            now = today = datetime.now()
            date = now.strftime("%Y-%m-%d")
            time = now.strftime("%H:%M:%S")
            completed = subprocess.run(
                    command,
                    input=f"****Credential****\n{date} {time}\n{credential}\n******************\n",
                    capture_output=True,
                    text=True,
                    )
            self.logger.debug(completed.stdout.replace("\n", ""))

    def _cleanup(self):
        if self.mqtt_client:
            self._disconnect()

    def loop(self):
        while self.running:
            self.mqtt_client.loop()
