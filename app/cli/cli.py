from app.services import UserSvc
from flask.cli import with_appcontext
import click


@click.command(name='delete-guest-accounts')
@click.argument('hours', type=int, required=False)
@with_appcontext
def delete_guest_accounts_command(hours: int):
    """
    Deletes guest accounts older than the specified retention window.

    Args:
        hours: The number of hours to retain guest data.
    """

    if hours is None:
        click.echo("Please provide up to how many hours you'd like to retain. Example: flask delete-guest-accounts 24")
        return

    try:
        affected_rows = UserSvc.delete_guest_accounts(hours)

    except ValueError:
        click.secho("There was a problem executing the delete command. Please try again.", fg='red')
        return

    if affected_rows >= 1:
        click.secho(
            f"Success! Deleted {affected_rows} guest account(s).",
            fg='green'
        )
    else:
        click.secho(
            "No guest accounts were deleted.",
            fg='yellow'
        )