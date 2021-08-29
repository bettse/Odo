from time import sleep
import asyncio
import base64
import json
import logging
import struct
import subprocess
import sys

from odo.models import BaseMqttDeviceModel

uuid = "fb0b57a2-8228-44cd-913a-94a122ba1206".replace('-', '')

topic_to_major = {
        "seen": "0001",
        "selected": "0002",
        "written": "0003",
        }
status_to_minor = {
        "": "0000",
        "pending": "0001",
        "success": "0002",
        "failure": "0003",
        }

class IBeacon(BaseMqttDeviceModel):
    def __init__(self, *args, **kwargs):
        super(IBeacon, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger('odo.iBeacon.iBeacon')
        self.state.payload.status = "connected"
        self.event_loop = asyncio.new_event_loop()
        self._subscribe_topics = [
            self.credential_topic["seen"],
            self.credential_topic["selected"],
            self.credential_topic["written"],
            self.command_topic
        ]

    def _handle_credential(self, msg=None):
        topic = msg.topic.split('/')
        status = ""
        if msg.topic == self.credential_topic['written']:
            message = json.loads(msg.payload)
            if "payload" in message:
                payload = message["payload"]
                if "status" in payload:
                    status = payload["status"]
        major = topic_to_major.get(topic[1], "0000")
        minor = status_to_minor.get(status, "0000")
        self.start_advertising(major, minor)

    def _handle_command(self, msg=None):
        self.logger.error(f"Command parsing not implemented")

    def _on_message(self, client, userdata, msg):
        self.logger.debug(f"MQTT message received-> {msg.topic} {str(msg.payload)}")
        if msg.topic in list(self.credential_topic.values()):
            self._handle_credential(msg=msg)
        if msg.topic == self.command_topic:
            self._handle_command(msg=msg)

    async def mqtt_loop(self):
        while True:
            if self.state.payload.status == "connected":
                self.mqtt_client.loop()
                await asyncio.sleep(0.5)
            else:
                await asyncio.sleep(10)

    def run_hci_cmd(self, cmd, hci="hci0", wait=1):
        self.logger.debug(f"Run HCI command {cmd}")
        cmd_ = ["hcitool", "-i", hci, "cmd"]
        cmd_ += cmd
        print(cmd_)
        subprocess.run(cmd_)
        if wait > 0:
            sleep(wait)

    def start_advertising(self, major, minor):
        adv = self.advertisement_template(major, minor)
        self.logger.debug(f"Start advertising: {self.bytes_to_strarray(adv)}")

        # Set BLE advertisement payload
        self.run_hci_cmd(["0x08", "0x0008"] + [format(len(adv), "x")] + self.bytes_to_strarray(adv))

        # Set BLE advertising mode
        hci_set_adv_params = ["0x08", "0x0006"]
        hci_set_adv_params += "a0", "00"
        hci_set_adv_params += "a0", "00"
        hci_set_adv_params += ["03", "00", "00", "00", "00", "00", "00", "00", "00"]
        hci_set_adv_params += ["07", "00"]
        self.run_hci_cmd(hci_set_adv_params)

        # Start BLE advertising
        self.run_hci_cmd(["0x08", "0x000a"] + ["01"], wait=0)

    def advertisement_template(self, major="0000", minor="0000"):
        adv = ""
        adv += "1a"  # length
        adv += "ff"  # manufacturer specific data
        adv += "4c00"  # company ID (Apple)
        adv += "0215"  # offline finding type and length
        adv += uuid
        adv += major
        adv += major
        adv += "00" # txPower
        return bytearray.fromhex(adv)

    def bytes_to_strarray(self, bytes_, with_prefix=False):
        if with_prefix:
            return [hex(b) for b in bytes_]
        else:
            return [format(b, "x") for b in bytes_]

    def _cleanup(self):
        pass

    def loop(self):
        self._send_state()
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_until_complete(self.mqtt_loop())
        self.event_loop.close()
