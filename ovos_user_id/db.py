import json
import os
from datetime import datetime
from typing import Iterable, List, Union, Dict

from ovos_config import Configuration
from ovos_config.locations import get_xdg_data_save_path
from ovos_utils.time import now_local
from sqlalchemy import Text, LargeBinary
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import MappedAsDataclass
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker

from ovos_bus_client.message import Message


class Base(MappedAsDataclass, DeclarativeBase):
    """subclasses will be converted to dataclasses"""


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(init=False, primary_key=True)  # this is present in message.context
    name: Mapped[str]
    discriminator: Mapped[str]  # the Identity type (i.e., user, agent, group, or role) of the Identity
    creation_date: Mapped[datetime] = mapped_column(insert_default=now_local, default=None)

    organization_id: Mapped[str] = mapped_column(default="")  # optional, mostly a placeholder
    aliases: Mapped[List[str]] = mapped_column(Text, default="[]")  # alt names for the user

    # security - at runtime, user aware skills can require a minimum auth level
    auth_level: Mapped[int] = mapped_column(default=0)  # arbitrary number assigned at creation time, 0 - 100

    # user_id
    # at runtime, this can be used by skills to increase auth_level
    auth_phrase: Mapped[str] = mapped_column(Text,
                                             default="")  # "voice password" for basic auth in non-sensitive operations
    voice_embeddings: Mapped[bytes] = mapped_column(LargeBinary, default=b"")  # binary data for voice embeddings
    face_embeddings: Mapped[bytes] = mapped_column(LargeBinary, default=b"")  # binary data for face embeddings
    voice_samples: Mapped[List[str]] = mapped_column(Text, default="[]")  # folder with audio files
    face_samples: Mapped[List[str]] = mapped_column(Text, default="[]")  # folder with image files

    # Location
    site_id: Mapped[str] = mapped_column(default="")  # in-doors
    city: Mapped[str] = mapped_column(default="")
    city_code: Mapped[str] = mapped_column(default="")
    region: Mapped[str] = mapped_column(default="")
    region_code: Mapped[str] = mapped_column(default="")
    country: Mapped[str] = mapped_column(default="")
    country_code: Mapped[str] = mapped_column(default="")
    timezone: Mapped[str] = mapped_column(default="")
    latitude: Mapped[float] = mapped_column(default=0.0)
    longitude: Mapped[float] = mapped_column(default=0.0)

    # preferences
    system_unit: Mapped[str] = mapped_column(default="metric")
    time_format: Mapped[str] = mapped_column(default="full")
    date_format: Mapped[str] = mapped_column(default="DMY")
    lang: Mapped[str] = mapped_column(default="")
    secondary_langs: Mapped[List[str]] = mapped_column(Text, default="[]")
    tts_config: Mapped[Dict[str, str]] = mapped_column(Text, default="{}")
    stt_config: Mapped[Dict[str, str]] = mapped_column(Text, default="{}")

    # contact info
    pgp_pubkey: Mapped[str] = mapped_column(default="")
    email: Mapped[str] = mapped_column(default="")
    phone_number: Mapped[str] = mapped_column(default="")

    # external_identifiers - eg, facebook_id, github_id... allow mapping users to other dbs
    external_identifiers: Mapped[Dict] = mapped_column(Text, default="{}")

    @property
    def as_dict(self) -> dict:
        # Exclude internal SQLAlchemy attributes and relationships
        list_keys = ["secondary_langs", "aliases", "external_identifiers",
                     "voice_samples", "face_samples",
                     "stt_config", "tts_config"]
        return {c.key: getattr(self, c.key)
                if c.key not in list_keys else json.loads(getattr(self, c.key))
                for c in inspect(self).mapper.column_attrs}


class UserDB:
    """default sqlite location: ~/.local/share/ovos_users/user_database.db

     remote databases can also be used, eg.
        mysql+mysqldb://scott:tiger@192.168.0.134/test?ssl_ca=/path/to/ca.pem&ssl_cert=/path/to/client-cert.pem&ssl_key=/path/to/client-key.pem

     any component that needs to get a user object (eg, skills) should have access to the user database
     """

    def __init__(self, db_path: str = None):
        if not db_path:
            os.makedirs(get_xdg_data_save_path('ovos_users'), exist_ok=True)
            db_path = f"sqlite:///{get_xdg_data_save_path('ovos_users')}/user_database.db"
        self.engine = create_engine(db_path)
        self.Session = sessionmaker(bind=self.engine)
        self.create_tables()

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def from_message(self, message: Message) -> dict:
        if "user_id" in message.context:
            uid = message.context["user_id"]
            return self.get_user(uid) or self.default_user
        else:
            return self.default_user

    @property
    def default_user(self) -> dict:
        cfg = Configuration()
        return User(
            name="default",
            discriminator="role",
            lang=cfg.get("lang", "en-us"),
            secondary_langs=json.dumps(cfg.get("secondary_langs", [])),
            time_format=cfg.get("time_format", "full"),
            date_format=cfg.get("date_format", "DMY"),
            systen_unit=cfg.get("system_unit", "metric"),

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
        ).as_dict

    def add_user(self, name: str, discriminator: str, **kwargs) -> dict:
        assert discriminator in ["user", "agent", "group", "role"]

        # Ensure list fields are converted to JSON string before storing
        for k in ["stt_config", "tts_config", 'secondary_langs', 'aliases',
                  'voice_samples', 'face_samples', 'external_identifiers']:
            if k in kwargs:
                kwargs[k] = json.dumps(kwargs[k])

        session = self.Session()
        try:
            new_user = User(name=name, discriminator=discriminator, **kwargs)
            session.add(new_user)
            session.commit()
            # Access attributes of new_user within the session scope
            print("Added user:", new_user.name, new_user.user_id)
            return new_user.as_dict
        except IntegrityError as e:
            session.rollback()
            print(e)
            raise ValueError("User already exists")  # Handle duplicate user error
        finally:
            session.close()

    def update_user(self, user_id: int, **kwargs) -> dict:
        session = self.Session()

        # Ensure list fields are converted to JSON string before storing
        for k in ["stt_config", "tts_config", 'secondary_langs', 'aliases',
                  'voice_samples', 'face_samples', 'external_identifiers']:
            if k in kwargs:
                kwargs[k] = json.dumps(kwargs[k])

        try:
            user = session.query(User).get(user_id)
            if user is None:
                raise ValueError("User not found")

            # Update fields from kwargs
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            session.commit()
            return user.as_dict
        except Exception as e:
            session.rollback()
            raise ValueError(f"Failed to update user: {str(e)}")
        finally:
            session.close()

    def delete_user(self, user_id: int):
        session = self.Session()
        try:
            user_to_delete = session.query(User).get(user_id)
            if user_to_delete:
                session.delete(user_to_delete)
                session.commit()
            else:
                raise ValueError("User not found")
        finally:
            session.close()

    def get_user(self, user_id: int) -> dict:
        session = self.Session()
        try:
            user = session.query(User).get(user_id)
            if not user:
                return None
            return user.as_dict
        finally:
            session.close()

    def find_user(self, name: str) -> List[dict]:
        session = self.Session()
        try:
            # Perform a case-insensitive search for users with matching names
            users = session.query(User).filter(func.lower(User.name) == func.lower(name)).all()
            return [u.as_dict for u in users]
        finally:
            session.close()

    def find_by_auth_phrase(self, auth_phrase: str) -> List[dict]:
        session = self.Session()
        try:
            # Perform a case-insensitive search for users with matching auth_phrase
            users = session.query(User).filter(func.lower(User.auth_phrase) == func.lower(auth_phrase)).all()
            return [u.as_dict for u in users]
        finally:
            session.close()

    def find_user_by_alias(self, alias: str) -> List[dict]:
        session = self.Session()
        try:
            users = session.query(User).filter(func.lower(User.name) == func.lower(alias)).all()
            # This assumes that aliases is a JSON-encoded list of strings
            users2 = session.query(User).filter(
                User.aliases.contains(f'"{alias}"')  # Note the inclusion of quotes for JSON string searching
            ).all()
            return [u.as_dict for u in users] + [u.as_dict for u in users2]
        finally:
            session.close()

    def find_by_external_id(self, id_string: Union[str, int]) -> List[dict]:
        id_string = str(id_string)

        session = self.Session()
        try:
            # This assumes that entity ids is JSON-encoded dict of strings
            users = session.query(User).filter(
                User.aliases.contains(f'"{id_string}"')  # Note the inclusion of quotes for JSON string searching
            ).all()
            return [u.as_dict for u in users]
        finally:
            session.close()

    def list_users(self) -> List[dict]:
        session = self.Session()
        try:
            # Query all users and retrieve their details
            users = session.query(User).all()
            return [user.as_dict for user in users]
        finally:
            session.close()

