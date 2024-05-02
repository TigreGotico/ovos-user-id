import struct
from typing import Optional
from ovos_bus_client.message import Message
from ovos_config import Configuration
import redis
import numpy as np


class RedisCameraReader:
    """access camera from https://github.com/OpenVoiceOS/ovos-PHAL-rediscamera"""
    def __init__(self, device_name: str):
        # Redis connection
        kwargs = Configuration().get("redis", {"host": "127.0.0.1", "port": 6379})
        self.r = redis.Redis(**kwargs)
        self.r.ping()
        self.name = "cam::" + device_name

    def get(self):
        """Retrieve Numpy array from Redis camera 'self.name' """
        encoded = self.r.get(self.name)
        h, w = struct.unpack('>II', encoded[:8])
        a = np.frombuffer(encoded, dtype=np.uint8, offset=8).reshape(h, w, 3)
        return a


class CameraManager:

    @staticmethod
    def from_message(message: Message) -> Optional[RedisCameraReader]:
        camera_id = message.context["camera_id"]
        return CameraManager.get(camera_id)

    @staticmethod
    def get(camera_id) -> Optional[RedisCameraReader]:
        host = Configuration().get("redis", {}).get("host", "127.0.0.1")
        return RedisCameraReader(camera_id, host)


if __name__ == "__main__":
    remote_cam = RedisCameraReader("laptop", "192.168.1.17")
    while True:
        frame = remote_cam.get()
        # do stuff