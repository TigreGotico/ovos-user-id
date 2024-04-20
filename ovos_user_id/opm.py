from typing import Optional, List

from ovos_plugin_manager.templates.transformers import MetadataTransformer, UtteranceTransformer
from ovos_utils.log import LOG

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovos_user_id.db import UserDB


def add_user2context(context: dict, db: UserDB) -> dict:
    """helper method to inject user preferences into the Session/message.context"""
    # update the session
    sess = Session.deserialize(context.get("session", {}))
    user = db.get_user(context["user_id"])
    if user:
        LOG.debug(f"updating session with user data: "
                  f"{user['user_id']} - {user['name']} - auth level: {user['auth_level']}")
        sess.lang = user["lang"] or sess.lang
        sess.site_id = user["site_id"] or sess.site_id
        sess.stt_preferences = user["stt_config"] or sess.stt_preferences
        sess.tts_preferences = user["tts_config"] or sess.tts_preferences
        sess.system_unit = user["system_unit"] or sess.system_unit
        sess.date_format = user["date_format"] or sess.date_format
        sess.time_format = user["time_format"] or sess.time_format
        sess.location_preferences = {
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
        context["session"] = sess.serialize()
    return context


class UserAuthPhrasePlugin(UtteranceTransformer):
    """detects auth_phrases and tags a user

    this is the simplest user recognition plugin"""
    def __init__(self, name="ovos-user-auth-phrase", priority=90):
        super().__init__(name, priority)
        self.db = UserDB()
        self.sess2user = {}

    def transform(self, utterances: List[str],
                  context: dict = None) -> (list, dict):
        if "user_id" in context:
            # do not overwrite previous user data
            return utterances, context

        for u in utterances:
            users = self.db.find_by_auth_phrase(u)
            # if user said pass phrase, tag the user
            if users:
                user = users[0]  # TODO - what if multiple matches
                sess = Session.deserialize(context.get("session", {}))
                self.sess2user[sess.session_id] = user["user_id"]
                context["user_id"] = user["user_id"]
                context = add_user2context(context, self.db)
                # TODO - play authentication sound/dialog ?
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
        self.db = UserDB()
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
        context = add_user2context(context, self.db)
        return context
