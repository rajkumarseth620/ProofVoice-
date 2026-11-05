"""
ProofVoice Internal Notification Gateway (No External Email Integration)
In accordance with system policy, external email services (SMTP, SendGrid, Resend, etc.) are disabled.
All operational alerts, registration notifications, and administrative updates are delivered
strictly inside the ProofVoice application via the Notification engine.
"""

import logging

logger = logging.getLogger(__name__)


def send_new_institution_request_email(request_obj):
    logger.info(f"Internal event: New institution registration request {request_obj.request_id} for {request_obj.institution_name}")
    return True


def send_institution_confirmation_email(request_obj):
    logger.info(f"Internal event: Institution registration confirmation for {request_obj.request_id}")
    return True


def send_student_onboarding_request_email(request_obj):
    logger.info(f"Internal event: Student onboarding inquiry {request_obj.request_id} for {request_obj.institution_name}")
    return True


def send_institution_approval_email(institution, recipient_email='', admin_name='', remarks=''):
    logger.info(f"Internal event: Institution {institution.name} workspace approved")
    return True


def send_institution_rejection_email(request_obj, reason=''):
    logger.info(f"Internal event: Institution request {request_obj.request_id} rejected. Reason: {reason}")
    return True


def send_institution_suspension_email(institution, reason=''):
    logger.info(f"Internal event: Institution {institution.name} workspace suspended. Reason: {reason}")
    return True
