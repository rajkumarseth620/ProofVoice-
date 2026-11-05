import uuid
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


class ChatConversation(models.Model):
    """
    Multi-turn conversation sessions for ProofVoice AI Assistant.
    Enforces strict user and multi-tenant isolation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_conversations',
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    title = models.CharField(max_length=255, default='New Chat')
    language = models.CharField(max_length=16, default='en-IN')
    intent_mode = models.CharField(max_length=32, default='GENERAL_KNOWLEDGE')
    summary = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        verbose_name = 'Chat Conversation'
        verbose_name_plural = 'Chat Conversations'
        ordering = ['-updated_at']

    def __str__(self):
        owner = self.user.email if self.user else f"Guest ({self.session_key[:8]})"
        return f"Chat '{self.title}' ({owner}) - {self.language}"


class ChatMessage(models.Model):
    """
    Individual message entry in a conversation with role, text, and voice metadata.
    """
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    )

    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    content = models.TextField()
    speak_text = models.TextField(blank=True, default='')
    topic = models.CharField(max_length=64, blank=True, default='general')
    language = models.CharField(max_length=16, default='en-IN')
    intent = models.CharField(max_length=32, default='GENERAL_KNOWLEDGE')
    audio_base64 = models.TextField(blank=True, default='')
    audio_url = models.URLField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role.upper()}] {self.content[:40]}..."

