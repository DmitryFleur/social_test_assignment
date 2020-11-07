from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone


@receiver(user_logged_in)
def user_login_signal(sender, request, user, **kwargs):
    user.last_login_datetime = timezone.now()
    user.save()
