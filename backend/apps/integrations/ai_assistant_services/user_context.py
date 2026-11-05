# -*- coding: utf-8 -*-
"""
User Context & Secure Campus Data Integration.
Enforces multi-tenant student privacy, retrieves live complaint progress from MySQL,
and provides contextual grounding for personal grievance queries.
"""
import logging

logger = logging.getLogger(__name__)

class UserContextService:
    @classmethod
    def get_user_summary(cls, user) -> dict:
        """
        Builds verified, privacy-isolated profile and complaint data for the authenticated user.
        """
        if not user or not getattr(user, 'is_authenticated', False):
            return {
                'authenticated': False,
                'name': 'Guest / Student',
                'role': 'Student',
                'institution': 'Campus Member',
                'complaints_count': 0,
                'active_complaints': [],
                'recent_status': None
            }

        name = getattr(user, 'full_name', '') or getattr(user, 'email', 'Student')
        role = getattr(user, 'role', 'STUDENT')
        inst_name = getattr(user, 'institution_name', 'Campus Member')

        # Query user complaints strictly scoped to request.user
        try:
            from apps.complaints.models import Complaint
            user_complaints = Complaint.objects.filter(student=user).order_by('-created_at')
            count = user_complaints.count()
            recent_list = []
            for c in user_complaints[:3]:
                recent_list.append({
                    'id': c.complaint_id,
                    'title': c.title,
                    'status': c.status,
                    'category': c.category.name if c.category else 'General',
                    'date': c.created_at.strftime('%b %d, %Y')
                })

            return {
                'authenticated': True,
                'name': name,
                'role': role,
                'institution': inst_name,
                'complaints_count': count,
                'active_complaints': recent_list,
                'recent_status': recent_list[0]['status'] if recent_list else None
            }
        except Exception as e:
            logger.warning(f"Error fetching user complaint context: {e}")
            return {
                'authenticated': True,
                'name': name,
                'role': role,
                'institution': inst_name,
                'complaints_count': 0,
                'active_complaints': [],
                'recent_status': None
            }
