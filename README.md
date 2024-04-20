## OVOS User ID Plugin

The OVOS User ID plugin allows skills in the OVOS system to retrieve user data based on the `user_id` included in bus messages.
Skills can access the user database to provide personalized experiences and interactions.

The `user_id` is assumed to be injected into `message.context` by external plugins, such as speaker_recognition or from hivemind

### Installation

Install the OVOS User ID plugin using pip:

```bash
pip install ovos-user-id
```

### Managing the User Database with CLI

Use the OVOS User ID CLI tool to perform various actions on the user database directly from the command line:

#### Local SQLite Database

By default, the OVOS User ID Plugin uses a local SQLite database located at `~/.local/share/ovos_users/user_database.db`. You can specify the path to this database using the `--db-path` option when executing commands.

#### Remote Databases (e.g., MySQL)

You can also configure the OVOS User ID Plugin to use remote databases, such as MySQL, by specifying the database connection URL. This allows you to store user data in a centralized location accessible to multiple OVOS instances.

Here is an example of using a MySQL database:

```bash
ovos-user-cli --db-path "mysql+mysqldb://username:password@host/database_name"
```

Replace the placeholders (`username`, `password`, `host`, and `database_name`) with your MySQL database credentials and connection details.

#### CLI Commands
- **Adding a New User**: Adds a new user to the database with specified details.

  ```bash
  ovos-user-cli add-user [name] [discriminator] [options]
  ```

- **Retrieving User Details**: Retrieves details of a user from the database.

  ```bash
  ovos-user-cli get-user [user_id]
  ```

- **Updating User Details**: Updates details of a user in the database.

  ```bash
  ovos-user-cli update-user [user_id] --field [field_name] --value [new_value]
  ```

- **Deleting a User**: Deletes a user from the database.

  ```bash
  ovos-user-cli delete-user [user_id]
  ```

- **Listing All Users**: Lists all users stored in the database.

  ```bash
  ovos-user-cli list-users
  ```

### Configuration

Configure the OVOS User ID plugin in the `mycroft.conf` file to enable user authentication and session management.

#### ovos-user-auth-phrase

This plugin detects authentication phrases spoken by users to identify them. 
When a phrase matches, the user is tagged, and their `user_id` is integrated into the bus  `message.context`.

  - **Functionality**:
    - Detects and matches user authentication phrases.
    - Tags users based on authentication phrases.
    - Integrates `user_id` information into the `message.context`.
  
  - **Integration**: 
    - On successful authentication, assigns a `user_id` to the `message.context` and emits a `ovos_users.auth_phrase.success` message with user information.


```json
"utterance_transformers": {
    "ovos-user-auth-phrase": {
      "db_path": "sqlite:////home/miro/.local/share/ovos_users/user_database.db"
    }
}
```

#### ovos-user-session-manager

This plugin modifies the current session based on user preferences stored in the database. 
As long as a message contains a `user_id` this plugin will access the user database and modify the current Session with the corresponding user preferences

  - **Functionality**:
    - Modifies the session based on user preferences.
    - Handles local and remote user sessions.
  
  - **Integration**:
    - Configurable to ignore default or remote sessions.
    - Updates session preferences such as language, location, and system preferences.


```json
"metadata_transformers": {
    "ovos-user-session-manager": {
        "ignore_default_session": true,
        "ignore_remote_sessions": false,
        "db_path": "mysql+mysqldb://username:password@host/database_name"
    }
}

```