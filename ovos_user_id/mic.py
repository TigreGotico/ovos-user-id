from typing import Optional
from ovos_bus_client.message import Message
from ovos_config import Configuration
import redis


class RedisMicReader:
    """access mic from https://github.com/OpenVoiceOS/ovos-...-redis-mic"""
    def __init__(self,  mic_id: str):
        # Redis connection
        kwargs = Configuration().get("redis", {"host": "127.0.0.1", "port": 6379})
        self.r = redis.Redis(**kwargs)
        self.r.ping()
        self.mic_id = mic_id

    def get(self):
        """Retrieve Numpy array from Redis mic 'self.name' """
        return self.r.get(self.mic_id)


class MicManager:

    @staticmethod
    def from_message(message: Message) -> Optional[RedisMicReader]:
        mic_id = message.context["mic_id"]
        return MicManager.get(mic_id)

    @staticmethod
    def get(mic_id) -> Optional[RedisMicReader]:
        return RedisMicReader(mic_id)


if __name__ == "__main__":
    remote_mic = RedisMicReader("laptop")
    while True:
        audio = remote_mic.get()
        # do stuff