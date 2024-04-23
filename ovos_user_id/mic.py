import struct
from typing import Optional
from ovos_bus_client.message import Message
from ovos_config import Configuration
from ovos_utils.log import LOG
try:
    import redis
    import numpy as np
    MICFEED_AVAILABLE = True
except ImportError:
    MICFEED_AVAILABLE = False


class RedisMicReader:
    """access mic from https://github.com/OpenVoiceOS/ovos-...-redis-mic"""
    def __init__(self,  device_name: str):
        if not MICFEED_AVAILABLE:
            LOG.error("remote microphone feed not available, please install 'redis' and 'numpy'")
            raise ImportError("redis/numpy not found")
        # Redis connection
        kwargs = Configuration().get("redis", {"host": "127.0.0.1", "port": 6379})
        self.r = redis.Redis(**kwargs)
        self.r.ping()
        self.name = "mic::" + device_name

    def get(self):
        """Retrieve Numpy array from Redis mic 'self.name' """
        encoded = self.r.get(self.name)
        h, w = struct.unpack('>II', encoded[:8])
        a = np.frombuffer(encoded, dtype=np.uint8, offset=8).reshape(h, w, 3)
        return a


class MicManager:

    @staticmethod
    def from_message(message: Message) -> Optional[RedisMicReader]:
        if not MICFEED_AVAILABLE:
            return None
        mic_id = message.context["mic_id"]
        return MicManager.get(mic_id)

    @staticmethod
    def get(mic_id) -> Optional[RedisMicReader]:
        if not MICFEED_AVAILABLE:
            return None
        return RedisMicReader(mic_id)


if __name__ == "__main__":
    remote_mic = RedisMicReader("laptop")
    while True:
        audio = remote_mic.get()
        # do stuff