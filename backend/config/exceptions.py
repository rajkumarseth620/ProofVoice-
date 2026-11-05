import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Sanitized REST Framework Exception Handler.
    Ensures that unexpected server errors (500) never leak database credentials,
    internal file paths, or sensitive debug stack traces in production API responses.
    """
    response = exception_handler(exc, context)

    if response is None:
        view = context.get('view')
        view_name = view.__class__.__name__ if view else 'APIView'
        logger.error(f"Internal unhandled exception in {view_name}: {str(exc)}", exc_info=True)

        if settings.DEBUG:
            error_message = f"Unhandled server error: {str(exc)}"
        else:
            error_message = "An internal server error occurred. Please contact platform support or try again later."

        return Response({
            'error': error_message,
            'status_code': 500
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
