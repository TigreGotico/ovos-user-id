from typing import Optional
from ovos_bus_client.message import Message
from ovos_config import Configuration
from ovos_utils.log import LOG
try:
    import redis
    MICFEED_AVAILABLE = True
except ImportError:
    MICFEED_AVAILABLE = False


class RedisMicReader:
    """access mic from https://github.com/OpenVoiceOS/ovos-...-redis-mic"""
    def __init__(self,  mic_id: str):
        if not MICFEED_AVAILABLE:
            LOG.error("remote microphone feed not available, please install 'redis'")
            raise ImportError("redis not found")
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