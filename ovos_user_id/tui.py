import click
from ovos_user_id.db import UserDB


@click.group()
@click.option("--db-path", default=None, help="Path to the SQLite user database.")
@click.pass_context
def cli(ctx, db_path):
    """Manage users in the database."""
    ctx.ensure_object(dict)
    ctx.obj["db"] = UserDB(db_path)


@cli.command()
@click.argument("name")
@click.argument("discriminator", default="user", type=click.Choice(["user", "agent", "group", "role"]))
@click.option("--organization-id", default="", help="Organization ID.")
@click.option("--aliases", default="[]", help="Alternate names (JSON format list).")
@click.option("--auth-level", default=0, type=int, help="Authentication level (0-100).")
@click.option("--auth-phrase", default="", help="Authentication phrase.")
@click.option("--voice-embeddings", default=b"", help="Voice embeddings (binary).")
@click.option("--face-embeddings", default=b"", help="Face embeddings (binary).")
@click.option("--voice-samples", default="[]", help="Voice samples (JSON format list of paths).")
@click.option("--face-samples", default="[]", help="Face samples (JSON format list of paths).")
@click.option("--site-id", default="", help="Site ID.")
@click.option("--city", default="", help="City.")
@click.option("--city-code", default="", help="City code.")
@click.option("--region", default="", help="Region.")
@click.option("--region-code", default="", help="Region code.")
@click.option("--country", default="", help="Country.")
@click.option("--country-code", default="", help="Country code.")
@click.option("--timezone", default="", help="Timezone.")
@click.option("--latitude", default=0.0, type=float, help="Latitude.")
@click.option("--longitude", default=0.0, type=float, help="Longitude.")
@click.option("--system-unit", default="metric", help="System unit.")
@click.option("--time-format", default="full", help="Time format.")
@click.option("--date-format", default="DMY", help="Date format.")
@click.option("--lang", default="", help="Language.")
@click.option("--secondary-langs", default="[]", help="Secondary languages (JSON format list of lang codes).")
@click.option("--tts-config", default="{}", help="TTS configuration (JSON format dict).")
@click.option("--stt-config", default="{}", help="STT configuration (JSON format dict).")
@click.option("--pgp-pubkey", default="", help="PGP public key.")
@click.option("--email", default="", help="Email.")
@click.option("--phone-number", default="", help="Phone number.")
@click.option("--external-identifiers", default="{}", help="External identifiers (JSON format dict).")
@click.pass_obj
def add_user(obj, name, discriminator, **kwargs):
    """Add a new user to the database."""
    user_data = {k.replace("-", "_"): v for k, v in kwargs.items() if v}
    try:
        user = obj["db"].add_user(name, discriminator, **user_data)
        click.echo(f"User '{user['name']}' added with ID: {user['user_id']}")
    except ValueError as e:
        click.echo(f"Error: {e}")


@cli.command()
@click.argument("user_id", type=int)
@click.pass_obj
def get_user(obj, user_id):
    """Retrieve user details from the database."""
    user = obj["db"].get_user(user_id)
    if user:
        click.echo(user)
    else:
        click.echo(f"User with ID '{user_id}' not found.")


@cli.command()
@click.argument("user_id", type=int)
@click.option("--field", default=None, help="Field to update.")
@click.option("--value", default=None, help="New value for the field.")
@click.pass_obj
def update_user(obj, user_id, field, value):
    """Update user details in the database."""
    if not field or not value:
        click.echo("Both --field and --value must be provided for updating.")
        return

    try:
        user = obj["db"].update_user(user_id, **{field.replace("_", "-"): value})
        click.echo(f"User '{user['name']}' updated successfully.")
    except ValueError as e:
        click.echo(f"Error: {e}")


@cli.command()
@click.argument("user_id", type=int)
@click.pass_obj
def delete_user(obj, user_id):
    """Delete a user from the database."""
    try:
        obj["db"].delete_user(user_id)
        click.echo(f"User with ID '{user_id}' deleted successfully.")
    except ValueError as e:
        click.echo(f"Error: {e}")


@cli.command()
@click.pass_obj
def list_users(obj):
    """List all users in the database."""
    users = obj["db"].list_users()
    if users:
        click.echo("List of users:")
        for user in users:
            click.echo(f"ID: {user['user_id']}, Name: {user['name']}")
    else:
        click.echo("No users found in the database.")


if __name__ == "__main__":
    cli()
