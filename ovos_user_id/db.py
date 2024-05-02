import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Union, Optional

import redis
from ovos_config import Configuration
from ovos_utils.time import now_local


@dataclass
class User:
    user_id: int  # this is present in message.context
    name: str
    discriminator: str  # the Identity type (i.e., user, agent, group, or role) of the Identity
    creation_date: datetime = field(default_factory=now_local)

    organization_id: str = ""
    aliases: List[str] = field(default_factory=list)  # alt names for the user

    # security - at runtime, user aware skills can require a minimum auth level
    auth_level: int = 0  # arbitrary number assigned at creation time, 0 - 100

    # at runtime, this can be used by skills to increase auth_level
    auth_phrase: str = ""  # "voice password" for basic auth in non-sensitive operations
    voice_embeddings: bytes = b""  # binary data for voice embeddings
    face_embeddings: bytes = b""  # binary data for face embeddings
    voice_samples: List[str] = field(default_factory=list)  # folder with audio files
    face_samples: List[str] = field(default_factory=list)  # folder with image files

    # Location
    site_id: str = ""  # in-doors
    city: str = ""
    city_code: str = ""
    region: str = ""
    region_code: str = ""
    country: str = ""
    country_code: str = ""
    timezone: str = ""
    latitude: float = 0.0
    longitude: float = 0.0

    # Preferences
    system_unit: str = "metric"  # Unit system preference
    time_format: str = "full"  # Time format preference
    date_format: str = "DMY"  # Date format preference
    lang: str = ""  # Language preference
    secondary_langs: List[str] = field(default_factory=list)  # Secondary languages
    tts_config: Dict[str, str] = field(default_factory=dict)  # Text-to-speech configuration
    stt_config: Dict[str, str] = field(default_factory=dict)  # Speech-to-text configuration

    # Contact information
    pgp_pubkey: str = ""  # PGP public key
    email: str = ""  # Email address
    phone_number: str = ""  # Phone number

    # external_identifiers - eg, facebook_id, github_id... allow mapping users to other dbs
    external_identifiers: Dict = field(default_factory=dict)

    @staticmethod
    def from_dict(user: dict) -> 'User':
        """Create a User object from a dictionary."""
        return User(**user)

    @staticmethod
    def from_json(user: str) -> 'User':
        """Create a User object from a JSON string."""
        return User.from_dict(json.loads(user))

    @property
    def as_dict(self) -> dict:
        """Convert User object to a dictionary."""
        return asdict(self)

    @property
    def as_json(self) -> str:
        """Convert User object to a JSON string."""
        return json.dumps(self.as_dict, sort_keys=True)


class UserDB:
    """Class for managing user data in Redis."""
    def __init__(self):
        """Initialize UserDB with Redis connection."""
        # Redis connection
        kwargs = Configuration().get("redis", {"host": "127.0.0.1", "port": 6379})
        self.r = redis.Redis(**kwargs)
        self.r.ping()

    @property
    def default_user(self) -> User:
        """Get the default user based on configuration."""
        cfg = Configuration()
        return User(
            user_id=0,
            name="default",
            discriminator="role",
            lang=cfg.get("lang", "en-us"),
            secondary_langs=cfg.get("secondary_langs", []),
            time_format=cfg.get("time_format", "full"),
            date_format=cfg.get("date_format", "DMY"),
            system_unit=cfg.get("system_unit", "metric"),

            city=cfg.get("location", {}).get("city", {}).get("name", ""),
            city_code=cfg.get("location", {}).get("city", {}).get("code", ""),
            region=cfg.get("location", {}).get("city", {}).get("state", {}).get("name", ""),
            region_code=cfg.get("location", {}).get("city", {}).get("state", {}).get("code", ""),
            country=cfg.get("location", {}).get("city", {}).get("state", {}).get("country", {}).get("name", ""),
            country_code=cfg.get("location", {}).get("city", {}).get("state", {}).get("country", {}).get("code", ""),

            latitude=cfg.get("location", {}).get("coordinate", {}).get("latitude", 0.0),
            longitude=cfg.get("location", {}).get("coordinate", {}).get("longitude", 0.0),
            timezone=cfg.get("location", {}).get("timezone", {}).get("code", ""),
            email=cfg.get("microservices", {}).get("email", {}).get("recipient", "")
        )

    def add_user(self, name: str, discriminator: str, **kwargs) -> User:
        """Add a new user to Redis."""
        assert discriminator in ["user", "agent", "group", "role"]

        new_user = User(user_id=self.count() + 1, name=name, discriminator=discriminator, **kwargs)
        self.r.set("user::" + str(new_user.user_id), new_user.as_json)
        print("Added user:", new_user.name, new_user.user_id)
        return new_user

    def update_user(self, user_id: int, **kwargs) -> User:
        """Update user information in Redis."""
        try:
            user = self.get_user(user_id)
            if not user:
                raise ValueError("User not found")

            # Update fields from kwargs
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            self.r.set("user::" + str(user.user_id), user.as_json)

            return user
        except Exception as e:
            raise ValueError(f"Failed to update user: {str(e)}")

    def delete_user(self, user_id: int):
        """Delete a user from Redis."""
        self.r.delete("user::" + str(user_id))

    def get_user(self, user_id: int) -> Optional[User]:
        """Get a user from Redis by user ID."""
        user: str = self.r.get("user::" + str(user_id))
        if user:
            return User.from_json(user)
        else:
            return None

    def find_user(self, name: str) -> List[User]:
        """Find users by name."""
        users = []
        for key in self.r.scan_iter("user::*"):
            user: str = self.r.get(key)
            if user and json.loads(user)['name'] == name:
                users.append(User.from_json(user))
        return users

    def find_by_auth_phrase(self, auth_phrase: str) -> List[User]:
        """Find users by authentication phrase."""
        users = []
        for key in self.r.scan_iter("user::*"):
            user: str = self.r.get(key)
            if user and json.loads(user)['auth_phrase'] == auth_phrase:
                users.append(User.from_json(user))
        return users

    def find_user_by_alias(self, alias: str) -> List[User]:
        """Find users by alias."""
        users = []
        for key in self.r.scan_iter("user::*"):
            user: str = self.r.get(key)
            if user and alias in json.loads(user)['aliases']:
                users.append(User.from_json(user))
        return users

    def find_by_external_id(self, id_string: Union[str, int]) -> List[User]:
        """Find users by external identifier."""
        users = []
        for key in self.r.scan_iter("user::*"):
            user: str = self.r.get(key)
            if user and str(id_string) in json.loads(user)['external_identifiers'].values():
                users.append(User.from_json(user))
        return users

    def list_users(self) -> List[User]:
        """List all users stored in Redis."""
        users = []
        for key in self.r.scan_iter("user::*"):
            user: str = self.r.get(key)
            if user:
                users.append(User.from_json(user))
        return users

    def count(self) -> int:
        return len(list(self.r.scan_iter("user::*")))