import os

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import User


@receiver(post_migrate)
def create_caelium_user(sender, **kwargs):
    """
    Signal handler to create a default Caelium user if it does not already exist.
    This function attempts to retrieve a user with the username "caelium". If the user does not exist,
    it creates a new user with predefined attributes such as username, email, name, avatar, location,
    gender, bio, birthdate, and password. The password is fetched from the environment variable
    "CAELIUM_PASSWORD".
    Args:
        sender (Any): The sender of the signal.
        **kwargs: Additional keyword arguments.
    Raises:
        ObjectDoesNotExist: If the user with the username "caelium" does not exist.
    """

    try:
        user = User.objects.get(username="caelium")
    except ObjectDoesNotExist:
        user = User.objects.create(
            username="caelium",
            email="app@caelium.co",
            name="Caelium",
            avatar="defaults/caelium.png",
            location="Cloud",
            gender="Other",
            bio="Welcome to the Caelium platform!",
            birthdate="2000-01-01",
            password=os.environ["CAELIUM_PASSWORD"],
        )
        user.set_password(user.password)
        user.save()
