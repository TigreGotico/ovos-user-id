from typing import Optional, List

from ovos_plugin_manager.templates.transformers import MetadataTransformer, UtteranceTransformer
from ovos_utils.log import LOG

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovos_user_id.cam import CameraManager
from ovos_user_id.db import UserManager


class UserAuthPhrasePlugin(UtteranceTransformer):
    """detects auth_phrases and tags a user

    this is the simplest user recognition plugin"""
    def __init__(self, name="ovos-user-auth-phrase", priority=90):
        super().__init__(name, priority)

    def transform(self, utterances: List[str],
                  context: dict = None) -> (list, dict):
        if "user_id" in context:
            # do not overwrite previous user data
            return utterances, context

        for u in utterances:
            users = UserManager.db.find_by_auth_phrase(u)
            # if user said pass phrase, tag the user
            if users:
                user = users[0]  # TODO - what if multiple matches
                LOG.info(f"User auth_phrase match! user_id: {user['user_id']}")
                sess = Session.deserialize(context.get("session", {}))
                sess = UserManager.assign2session(user["user_id"],
                                                  session_id=sess.session_id)
                context["session"] = sess.serialize()
                context["user_id"] = user["user_id"]
                # companion skill can speak on this event
                self.bus.emit(Message("ovos_users.auth_phrase.success",
                                      {"user_id": user["user_id"],
                                       "name": user["name"]}),
                              context)
                return [], context  # consume utterance

        return utterances, context


class UserSessionPlugin(MetadataTransformer):
    """
    this plugin can be used to modify the current session based on user preferences

    It can run in ovos-core (on-device user id) or in hivemind-core (bridges/satellites)
    """

    def __init__(self, name="ovos-user-session-manager", priority=90):
        super().__init__(name, priority)
        # plugin can be configured to only handle local users (eg, speaker recognition)
        # vs remote users (eg, sent by hivemind)
        self.ignore_default_session = self.config.get("ignore_default_session", False)
        self.ignore_remote_sessions = self.config.get("ignore_remote_sessions", False)

    def transform(self, context: Optional[dict] = None) -> dict:
        if "user_id" not in context:
            return context
        # update the session
        sess = Session.deserialize(context.get("session", {}))
        if self.ignore_default_session and sess.session_id == "default":
            # typically user_id was assigned by a user recognition plugin
            return context
        elif self.ignore_remote_sessions and sess.session_id != "default":
            # typically user_id was assigned by a hivemind client
            return context

        sess = UserManager.assign2session(user_id=context["user_id"],
                                          session_id=sess.session_id)
        context["session"] = sess.serialize()
        return context


class UserFaceAuthPlugin(MetadataTransformer):
    """performs face recognition if a camera_id is assigned to the message.context"""

    def __init__(self, name="ovos-user-face-auth", priority=50):
        super().__init__(name, priority)
        self.face_recognizer = None  # TODO - face recognition plugin

    def transform(self, context: dict = None) -> dict:
        if "user_id" in context:
            # do not overwrite previous user data
            return context

        camera_id = context.get("camera_id")
        if not camera_id:
            return context

        cam = CameraManager.get(camera_id)
        frame = cam.get()
        if self.face_recognizer:
            faces = self.face_recognizer.recognize(frame)
            if faces:
                user = faces[0]  # TODO - what if multiple matches
                LOG.info(f"User face match! user_id: {user['user_id']}")
                sess = Session.deserialize(context.get("session", {}))
                sess = UserManager.assign2session(user["user_id"],
                                                  session_id=sess.session_id)
                context["session"] = sess.serialize()
                context["user_id"] = user["user_id"]
                # companion skill can speak on this event
                self.bus.emit(Message("ovos_users.face_auth.success",
                                      {"user_id": user["user_id"],
                                       "name": user["name"]}),
                              context)

        return context
