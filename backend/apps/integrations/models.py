from django.db import models
from django.conf import settings
from apps.institutions.models import Institution

class AuditLog(models.Model):
    """
    Security and administrative action audit trail.
    Records administrative interventions, status changes, and access permissions.
    """
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_actions'
    )
    action = models.CharField(max_length=100, db_index=True)
    target_model = models.CharField(max_length=100)
    target_id = models.CharField(max_length=100)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']

    def __str__(self):
        actor_email = self.actor.email if self.actor else 'System'
        return f"[{self.action}] by {actor_email} on {self.target_model}:{self.target_id} at {self.timestamp}"
