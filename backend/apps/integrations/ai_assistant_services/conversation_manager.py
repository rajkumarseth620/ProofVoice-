# -*- coding: utf-8 -*-
"""
ProofVoice Conversation Manager.
Handles database persistence of multi-turn conversation sessions and messages.
Enforces strict multi-tenant and user isolation:
- Authenticated users access only their own conversation sessions.
- Guest users are safely segregated via session keys.
- Supports New Chat, Retrieval, Context Window pruning, and Session Deletion.
"""

import uuid
import logging
from django.utils import timezone
from apps.integrations.models import ChatConversation, ChatMessage

logger = logging.getLogger(__name__)

class ConversationManager:

    @classmethod
    def get_or_create_conversation(cls, conversation_id=None, user=None, session_key='', title='New Chat', language='en-IN', intent_mode='GENERAL_KNOWLEDGE'):
        """
        Retrieves an existing conversation or creates a new one.
        Ensures strict ownership verification.
        """
        if conversation_id:
            try:
                # If UUID string or UUID object
                if isinstance(conversation_id, str):
                    conv_uuid = uuid.UUID(conversation_id)
                else:
                    conv_uuid = conversation_id

                conv = ChatConversation.objects.filter(id=conv_uuid).first()
                if conv:
                    # Verify ownership if user is authenticated
                    if user and getattr(user, 'is_authenticated', False):
                        if conv.user and conv.user != user:
                            logger.warning(f"Security Alert: User {user.email} attempted to access conversation {conv.id} owned by {conv.user.email}")
                            # Create an isolated conversation for this user
                            conv = ChatConversation.objects.create(
                                user=user,
                                title=title,
                                language=language,
                                intent_mode=intent_mode
                            )
                        elif not conv.user:
                            # Attach guest conversation to newly logged-in user
                            conv.user = user
                            conv.save(update_fields=['user'])
                    return conv
            except Exception as e:
                logger.warning(f"Invalid conversation_id '{conversation_id}': {e}")

        # Create new conversation
        conv = ChatConversation.objects.create(
            user=user if (user and getattr(user, 'is_authenticated', False)) else None,
            session_key=session_key or '',
            title=title or 'New Chat',
            language=language or 'en-IN',
            intent_mode=intent_mode or 'GENERAL_KNOWLEDGE'
        )
        return conv

    @classmethod
    def save_message(cls, conversation, role: str, content: str, speak_text: str = '', topic: str = 'general', language: str = 'en-IN', intent: str = 'GENERAL_KNOWLEDGE', audio_base64: str = '', audio_url: str = ''):
        """
        Appends a message to the conversation and updates conversation metadata.
        """
        if not conversation:
            return None

        msg = ChatMessage.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            speak_text=speak_text or '',
            topic=topic or 'general',
            language=language or conversation.language,
            intent=intent or conversation.intent_mode,
            audio_base64=audio_base64 or '',
            audio_url=audio_url or ''
        )

        # Update conversation title from first user message if still default
        if role == 'user' and (conversation.title == 'New Chat' or not conversation.title):
            words = content.strip().split()
            auto_title = " ".join(words[:6])
            if len(words) > 6:
                auto_title += "..."
            conversation.title = auto_title[:80]

        conversation.language = language or conversation.language
        conversation.intent_mode = intent or conversation.intent_mode
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['title', 'language', 'intent_mode', 'updated_at'])

        return msg

    @classmethod
    def get_conversation_history(cls, conversation, max_turns: int = 10) -> list:
        """
        Retrieves normalized history turns for multi-turn AI context.
        """
        if not conversation:
            return []

        qs = conversation.messages.order_by('created_at')
        total_msgs = qs.count()

        # Prune context window if conversation is very long
        if total_msgs > max_turns * 2:
            qs = qs[total_msgs - (max_turns * 2):]

        history = []
        for msg in qs:
            history.append({
                'role': msg.role,
                'content': msg.content,
                'topic': msg.topic,
                'language': msg.language,
                'created_at': msg.created_at.isoformat()
            })
        return history

    @classmethod
    def list_user_conversations(cls, user=None, session_key='', limit: int = 20) -> list:
        """
        Returns a list of conversation sessions for the user with strict isolation.
        """
        if user and getattr(user, 'is_authenticated', False):
            qs = ChatConversation.objects.filter(user=user)
        elif session_key:
            qs = ChatConversation.objects.filter(session_key=session_key, user__isnull=True)
        else:
            return []

        results = []
        for conv in qs.order_by('-updated_at')[:limit]:
            msg_count = conv.messages.count()
            results.append({
                'id': str(conv.id),
                'title': conv.title,
                'language': conv.language,
                'intent_mode': conv.intent_mode,
                'message_count': msg_count,
                'created_at': conv.created_at.strftime('%b %d, %Y, %I:%M %p') if conv.created_at else '',
                'updated_at': conv.updated_at.strftime('%b %d, %Y, %I:%M %p') if conv.updated_at else ''
            })
        return results

    @classmethod
    def delete_conversation(cls, conversation_id, user=None, session_key='') -> bool:
        """
        Deletes a conversation session safely with strict ownership verification.
        """
        try:
            conv_uuid = uuid.UUID(str(conversation_id))
            conv = ChatConversation.objects.filter(id=conv_uuid).first()
            if not conv:
                return False

            if user and getattr(user, 'is_authenticated', False):
                if conv.user != user:
                    return False
            elif session_key:
                if conv.session_key != session_key or conv.user is not None:
                    return False
            else:
                return False

            conv.delete()
            return True
        except Exception as e:
            logger.warning(f"Error deleting conversation {conversation_id}: {e}")
            return False
