## OVOS User ID Service

**WIP** this repo is a work in progress
_________________

- [OVOS User ID Service](#ovos-user-id-service)
  * [Installation](#installation)
  * [Pre Requisites](#pre-requisites)
    + [SQL](#sql)
    + [Redis](#redis)
  * [Plugins](#plugins)
    + [Redis Microphone](#redis-microphone)
    + [Redis Camera](#redis-camera)
    + [User Session Manager](#user-session-manager)
  * [Authentication Mechanisms](#authentication-mechanisms)
    + [Auth Phrase](#auth-phrase)
    + [Speaker Recognition](#speaker-recognition)
    + [Face Recognition](#face-recognition)
  * [The User Database - CLI Commands](#cli-commands)


The OVOS User ID service allows skills in the OVOS system to retrieve user data based on the `user_id` included in bus messages.
Skills can access the user database to provide personalized experiences and interactions.

User recognition is handled by a `metadata transformer` plugin, which interfaces with the `ovos-user-id` service (this repo) to inject `user_id` into `message.context`

The `user_id` can also be injected into `message.context` out of the box by external clients, such as hivemind

### Installation

Install the OVOS User ID plugin using pip:

```bash
pip install ovos-user-id
```

### Pre Requisites

#### Redis

for voice and face recognition a companion Redis server needs to be running, this is used to store arbitrary binary data

This is where buffers for mic and camera data are stored, allowing access to remote cameras/mic data from several devices

a OVOS skill can then access a specific camera/microphone by id by retrieving the feed from redis

```json
{
  "redis": {
    "host": "my-redis.cloud.redislabs.com",
    "port": 6379,
    "username": "default",
    "password": "secret",
    "ssl": true,
    "ssl_certfile": "./redis_user.crt",
    "ssl_keyfile": "./redis_user_private.key",
    "ssl_ca_certs": "./redis_ca.pem"
  }
}
```

### Plugins

#### Redis Microphone

In dinkum-listener/voice-sat install [ovos-redis-mic-plugin](https://github.com/JarbasHiveMind/ovos-redis-mic-plugin), then `mic_id` will be available in the `message.context`

This companion `audio transformer` plugin is responsible for storing the last STT audio in redis

```python
"listener": {
    "audio_transformers": {
        "ovos-redis-mic-plugin": {}
    }
}
```

> `mic_id` is of the format `mic::{session_id}`

#### Redis Camera

Devices/Satellites can run [ovos-PHAL-rediscamera](https://github.com/OpenVoiceOS/ovos-PHAL-rediscamera) plugin, this plugin will publish the camera feed to redis that can then be accessed by skills with vision capabilities

the feed is accessible by a `camera_id` injected in the `message.context`

```json
{
  "PHAL": {
    "ovos-PHAL-rediscamera": {
      "device_name": "my_phal_device",
      "camera_index": 0
    }
  }
}
```
> `camera_id` is of the format `cam::{device_name}`

TODO - add `camera_id` to Session, default to reading from `mycroft.conf` ovos-PHAL-rediscamera config


#### User Session Manager

this metadata transformer plugin maps `user_id`s to `session_id`s, depending on the current session it will ensure the correct `user_id` is also present in `message.context`.

This plugin optionally also modifies the session data to inject user preferences (such as location and system_unit)

As long as a message contains a `session_id` and this plugin has a mapped `user_id` to that session, 
this plugin will access the redis user database and modify the current Session with the corresponding user preferences

**Functionality**
  - Associates `user_id`s with `session_id`s
  - Modifies the session based on user preferences.
  - Configurable to ignore default or remote sessions.
  - Updates session preferences such as language, location, and system preferences.

```json
"metadata_transformers": {
    "ovos-user-session-manager": {
        "ignore_default_session": true,
        "ignore_remote_sessions": false
    }
}
```

### Authentication Mechanisms

Skills can use the `UserManager` class to retrieve user info

user data can be retrieved at any point from a message

```python
user_data = UserManager.from_message(message)
user_id = user_data["user_id"]  # see ovos_user_id.db for details of available keys
```

the `authenticate` method will check available data and return a score between 0 (NOT the user!) to 100 (absolutely certain this is the user)

This score is assigned based on the various auth mechanisms available (face, voice, secret...)

```python
auth_phrase = self.get_response("identify yourself")
auth_level = UserManager.authenticate(user_id, camera_id, auth_phrase)
assert 0 <= auth_level <= 100
```

This metric is still being defined, but values above 50 should indicate a proper user match, it is up to individual skills to require a proper threshold based on the action being performed

> "play my favorite jams" and "empty my bank account" have very different security concerns and `auth_level` is just a piece of the equation

#### Auth Phrase

Via the companion skill a user can speak his secret `auth_phrase`, this will assign the corresponding `user_id` to a session

TODO - companion skill

#### Speaker Recognition

The last STT audio is accessible in redis via the `mic_id` injected in the `message.context`, usually of the format `mic::{session_id}`

The speaker recognition plugin can then operate on specific `mic_id` to validate or assign a `user_id`

> `mic_id` might not be present in the `message.context`, the companion listener **plugin is needed** to ensure it is present

TODO - companion recognition plugin (loaded in this repo)

#### Face Recognition

The face recognition plugin can then operate on specific `camera_id` to validate or assign a `user_id`

TODO - companion plugin (loaded in this repo)

> `camera_id` might not be present in the `message.context`, the companion metadata plugin is needed to ensure it is present


### The User Database -  CLI Commands

- **Adding a New User**: Adds a new user to redis with specified details.

  ```bash
  ovos-user-cli add-user [name] [discriminator] [options]
  ```

- **Retrieving User Details**: Retrieves details of a user from redis.

  ```bash
  ovos-user-cli get-user [user_id]
  ```

- **Updating User Details**: Updates details of a user in redis.

  ```bash
  ovos-user-cli update-user [user_id] --field [field_name] --value [new_value]
  ```

- **Deleting a User**: Deletes a user from redis.

  ```bash
  ovos-user-cli delete-user [user_id]
  ```

- **Listing All Users**: Lists all users stored in redis.

  ```bash
  ovos-user-cli list-users
  ```
