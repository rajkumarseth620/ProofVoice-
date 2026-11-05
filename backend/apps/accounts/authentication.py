from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions

TOKEN_EXPIRATION_DAYS = getattr(settings, 'TOKEN_EXPIRATION_DAYS', 30)


class ExpiringTokenAuthentication(TokenAuthentication):
    """
    Extends standard DRF TokenAuthentication with automatic token age validation.
    Tokens older than TOKEN_EXPIRATION_DAYS (default 30 days) are safely revoked
    and rejected, enforcing regular re-authentication.
    """
    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid or unrecognized authentication token.')

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed('User account is suspended, inactive or disabled.')

        if token.created and (timezone.now() - token.created) > timedelta(days=TOKEN_EXPIRATION_DAYS):
            token.delete()
            raise exceptions.AuthenticationFailed('Authentication token has expired. Please sign in again.')

        return (token.user, token)
