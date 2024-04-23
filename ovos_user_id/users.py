from ovos_user_id.db import UserDB
from ovos_user_id.cam import CameraManager
from ovos_user_id.mic import MicManager
from ovos_user_id.templates import FaceRecognizer, VoiceRecognizer
from ovos_bus_client.session import Session, SessionManager
from ovos_bus_client.message import Message
from ovos_utils.log import LOG
from typing import Optional, Dict


class UserManager:
    db: UserDB = UserDB()
    face_recognizer: FaceRecognizer = None
    voice_recognizer: VoiceRecognizer = None
    sess2user: dict = {}

    @classmethod
    def bind(cls, face_rec: FaceRecognizer,
             voice_rec: VoiceRecognizer):
        # TODO - expose these via a bus api instead
        # allow a dedicated service to run the plugins, avoiding multiple in memory plugins
        cls.face_recognizer = face_rec
        cls.voice_recognizer = voice_rec

    @staticmethod
    def from_message(message: Message) -> Optional[dict]:
        uid = message.context.get("user_id", "unknown")
        if uid == "unknown":
            return None
        assert uid.isdigit()  # validate
        return UserManager.db.get_user(int(uid))

    @staticmethod
    def assign2session(user_id: int, session_id: str) -> Session:
        user = (UserManager.db.get_user(user_id) or
                UserManager.db.default_user)
        if session_id and session_id in SessionManager.sessions:
            sess = SessionManager.sessions[session_id]
        else:
            sess = Session(session_id=session_id)
        sess.location_prefs = {
            "coordinate": {"latitude": user["latitude"],
                           "longitude": user["longitude"]},
            "timezone": {"code": user["timezone"],
                         "name": user["timezone"]},
            "city": {"code": user["city_code"],
                     "name": user["city"],
                     "region": {
                         "code": user["region_code"],
                         "name": user["region"],
                         "country": {"name": user["country"],
                                     "code": user["country_code"]}
                     }
                     }
        }
        # sess.lang = user["lang"] # not lang as lang is set before STT, this plugin runs after STT
        sess.date_format = user["date_format"]
        sess.time_format = user["time_format"]
        sess.system_unit = user["system_unit"]
        SessionManager.update(sess)
        UserManager.sess2user[sess.session_id] = user_id
        LOG.debug(f"assigned user_id: {user_id} to session: {sess.session_id}")
        return sess

    @staticmethod
    def authenticate(user_id, camera_id, auth_phrase: Optional[str] = None) -> int:
        """skills should use this to get a auth level"""
        auth_level = 0

        user = UserManager.db.get_user(user_id)
        if not user:
            return 0

        # if face match increase auth level
        cam = CameraManager.get(camera_id)
        if cam and UserManager.face_recognizer:
            frame = cam.get()
            preds: Dict[str, float] = UserManager.face_recognizer.predict(frame, top_k=3)
            uid, conf = max(preds.items(), key=lambda k: k[1])
            if uid == user_id:
                auth_level += 30

        # if voice match increase auth level
        mic = MicManager.get(camera_id)
        if mic and UserManager.voice_recognizer:
            frame = mic.get()
            preds: Dict[str, float] = UserManager.voice_recognizer.predict(frame, top_k=3)
            uid, conf = max(preds.items(), key=lambda k: k[1])
            if uid == user_id:
                auth_level += 30

        # user secret phrase is known
        if auth_phrase and auth_phrase == user.get("auth_phrase"):
            auth_level += 15

        return auth_level
