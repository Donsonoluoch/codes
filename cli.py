import click
from app import create_app
from models import db, User

@click.group()
def cli():
    """A collection of commands for managing the application."""
    pass

@cli.command('create-admin')
@click.argument('name')
@click.argument('email')
@click.argument('password')
def create_admin_command(name, email, password):
    """Creates a new admin user."""
    app = create_app()
    with app.app_context():
        if User.query.filter_by(email=email).first():
            click.echo(f"Error: User with email '{email}' already exists.")
            return

        new_admin = User(name=name, email=email, user_type='admin')
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()
        click.echo(f"Admin user ({email}) created successfully!")

if __name__ == '__main__':
    cli()
