# -*- coding: utf-8 -*-
"""
ProofVoice Authenticated Database Intelligence Service.
Provides controlled, read-only ORM queries for authenticated student & administrator accounts.
Enforces strict multi-tenant isolation and user data privacy:
- Students can only view their own complaints, submissions, and notifications.
- Administrators can only view complaints within their verified institution.
- Never executes arbitrary SQL generated from user messages.
"""

import logging
from django.utils import timezone
from apps.complaints.models import Complaint
from apps.notifications.models import Notification
from apps.accounts.models import StudentProfile, AdministratorProfile

logger = logging.getLogger(__name__)

class CampusDatabaseService:

    @classmethod
    def get_user_complaints_summary(cls, user) -> dict:
        """
        Returns a verified, multi-tenant-safe summary of complaints for the authenticated user.
        """
        if not user or not getattr(user, 'is_authenticated', False):
            return {
                'authenticated': False,
                'message': "User is not authenticated. Please log in to view active complaints."
            }

        # Role-based query filtering
        if getattr(user, 'role', '') == 'STUDENT':
            qs = Complaint.objects.filter(student=user).select_related('institution', 'assigned_department', 'category')
        elif getattr(user, 'role', '') in ['ADMIN', 'SUPER_ADMIN']:
            if getattr(user, 'institution', None):
                qs = Complaint.objects.filter(institution=user.institution).select_related('student', 'assigned_department', 'category')
            else:
                qs = Complaint.objects.none()
        else:
            qs = Complaint.objects.filter(assigned_to=user).select_related('student', 'assigned_department', 'category')

        total = qs.count()
        submitted = qs.filter(status='SUBMITTED').count()
        under_review = qs.filter(status='UNDER_REVIEW').count()
        in_progress = qs.filter(status='IN_PROGRESS').count()
        resolved = qs.filter(status='RESOLVED').count()
        escalated = qs.filter(status='ESCALATED').count()

        active_count = submitted + under_review + in_progress + escalated

        recent = []
        for c in qs.order_by('-created_at')[:5]:
            recent.append({
                'id': c.complaint_id or f"PV-{c.id}",
                'title': c.title,
                'status': c.status,
                'category': c.category.name if c.category else 'General',
                'assigned_department': c.assigned_department.name if c.assigned_department else 'Campus IT Services',
                'submitted_at': c.created_at.strftime('%b %d, %Y, %I:%M %p') if c.created_at else 'Recent',
                'is_resolved': c.status == 'RESOLVED'
            })

        return {
            'authenticated': True,
            'user_email': user.email,
            'role': getattr(user, 'role', ''),
            'total_count': total,
            'active_count': active_count,
            'counts_by_status': {
                'submitted': submitted,
                'under_review': under_review,
                'in_progress': in_progress,
                'resolved': resolved,
                'escalated': escalated
            },
            'recent_complaints': recent
        }

    @classmethod
    def get_latest_complaint(cls, user) -> dict:
        """
        Returns the latest submitted complaint for the authenticated user.
        """
        if not user or not getattr(user, 'is_authenticated', False):
            return {'found': False, 'error': 'Authentication required.'}

        if getattr(user, 'role', '') == 'STUDENT':
            c = Complaint.objects.filter(student=user).order_by('-created_at').first()
        elif getattr(user, 'role', '') in ['ADMIN', 'SUPER_ADMIN'] and getattr(user, 'institution', None):
            c = Complaint.objects.filter(institution=user.institution).order_by('-created_at').first()
        else:
            c = Complaint.objects.filter(assigned_to=user).order_by('-created_at').first()

        if not c:
            return {'found': False, 'message': 'No complaints on record.'}

        return {
            'found': True,
            'id': c.complaint_id or f"PV-{c.id}",
            'title': c.title,
            'status': c.status,
            'category': c.category.name if c.category else 'General',
            'assigned_department': c.assigned_department.name if c.assigned_department else 'Campus IT Services',
            'submitted_at': c.created_at.strftime('%b %d, %Y, %I:%M %p') if c.created_at else 'Recently',
            'is_resolved': c.status == 'RESOLVED'
        }

    @classmethod
    def get_specific_complaint(cls, user, complaint_ref: str) -> dict:
        """
        Retrieves a specific complaint with strict ownership/tenant checks.
        """
        if not user or not getattr(user, 'is_authenticated', False):
            return {'found': False, 'error': 'Authentication required.'}

        clean_ref = (complaint_ref or '').strip()
        if not clean_ref:
            return {'found': False, 'error': 'No complaint reference provided.'}

        # Query by complaint_id or pk
        if clean_ref.isdigit():
            c = Complaint.objects.filter(pk=int(clean_ref)).select_related('student', 'institution', 'assigned_department', 'category').first()
        else:
            c = Complaint.objects.filter(complaint_id=clean_ref).select_related('student', 'institution', 'assigned_department', 'category').first()

        if not c:
            return {'found': False, 'error': f"Complaint with ID '{clean_ref}' not found."}

        # Authorization check: Student can only view their own complaint
        if getattr(user, 'role', '') == 'STUDENT' and c.student != user:
            logger.warning(f"Security Alert: User {user.email} attempted unauthorized access to complaint {clean_ref}")
            return {'found': False, 'error': "Access denied. You can only view your own complaints."}

        # Multi-tenant check for Admins
        if getattr(user, 'role', '') in ['ADMIN', 'SUPER_ADMIN'] and user.institution and c.institution != user.institution:
            return {'found': False, 'error': "Access denied. Complaint belongs to another institution."}

        return {
            'found': True,
            'id': c.complaint_id or f"PV-{c.id}",
            'title': c.title,
            'status': c.status,
            'priority': c.priority,
            'category': c.category.name if c.category else 'General',
            'assigned_department': c.assigned_department.name if c.assigned_department else 'Campus IT Services',
            'created_at': c.created_at.strftime('%b %d, %Y, %I:%M %p') if c.created_at else '',
            'updated_at': c.updated_at.strftime('%b %d, %Y, %I:%M %p') if c.updated_at else '',
            'resolution_notes': c.resolution_notes or '',
            'is_resolved': c.status == 'RESOLVED'
        }

    @classmethod
    def get_user_notifications_summary(cls, user) -> dict:
        """
        Retrieves personal notifications for the authenticated user with strict user isolation.
        """
        if not user or not getattr(user, 'is_authenticated', False):
            return {'authenticated': False, 'unread_count': 0, 'total_count': 0, 'notifications': []}

        qs = Notification.objects.filter(recipient=user).order_by('-created_at')
        unread_count = qs.filter(is_read=False).count()

        recent = []
        for n in qs[:5]:
            recent.append({
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'is_read': n.is_read,
                'created_at': n.created_at.strftime('%b %d, %I:%M %p') if n.created_at else ''
            })

        return {
            'authenticated': True,
            'unread_count': unread_count,
            'total_count': qs.count(),
            'recent_notifications': recent
        }

    @classmethod
    def get_user_profile_summary(cls, user) -> dict:
        """
        Retrieves verified student or administrator profile information.
        """
        if not user or not getattr(user, 'is_authenticated', False):
            return {'authenticated': False, 'error': 'Authentication required.'}

        res = {
            'authenticated': True,
            'name': user.full_name or user.email,
            'email': user.email,
            'role': getattr(user, 'role', ''),
            'is_verified': getattr(user, 'is_verified', False),
            'institution': '',
            'assigned_department': '',
            'student_id': '',
            'course': '',
            'semester': '',
            'phone': '',
            'address': ''
        }

        if getattr(user, 'role', '') == 'STUDENT':
            sp = StudentProfile.objects.filter(user=user).select_related('institution').first()
            if sp:
                res['institution'] = sp.institution.name if sp.institution else 'Campus Institution'
                res['assigned_department'] = sp.department or 'General'
                res['student_id'] = sp.student_id or 'N/A'
                res['course'] = sp.course or 'Undergraduate'
                res['semester'] = sp.semester or 'Current'
                res['phone'] = sp.phone or ''
                res['address'] = sp.address or ''
        elif getattr(user, 'role', '') in ['ADMIN', 'SUPER_ADMIN']:
            ap = AdministratorProfile.objects.filter(user=user).select_related('institution').first()
            if ap:
                res['institution'] = ap.institution.name if ap.institution else 'Campus Institution'
                res['assigned_department'] = ap.department_name or 'Administration'
                res['designation'] = ap.designation or 'Administrator'

        return res

    @classmethod
    def format_complaints_response(cls, summary: dict, lang: str = 'en-IN') -> dict:
        """
        Formats user complaints summary into rich localized text with audio speak text.
        """
        if not summary.get('authenticated'):
            return {
                'reply': (
                    "**How to Check Your Active Complaints:**\n\n"
                    "1. Log in to your student dashboard using your institutional email and password (`login.html`).\n"
                    "2. Click on **'My Complaints'** in the left sidebar menu (`my-complaints.html`).\n"
                    "3. You will see a live breakdown of all your filed grievances along with real-time status badges (**Submitted**, **Under Review**, **In Progress**, **Resolved**).\n"
                    "4. Click **'View Details'** on any complaint to read administrative responses, track technician assignments, or edit/delete your application."
                ),
                'speak_text': "To check your complaints, log in and navigate to My Complaints in the left sidebar menu.",
                'topic': 'complaint_tracking_instructions',
                'language': lang,
                'suggested_actions': ["Log In to Dashboard", "Create Complaint", "Help & Support"]
            }

        total = summary.get('total_count', 0)
        active = summary.get('active_count', 0)
        recent = summary.get('recent_complaints', [])

        if total == 0:
            replies = {
                'hi-IN': "आपके खाते में अभी तक कोई शिकायत दर्ज नहीं है। नई समस्या रिपोर्ट करने के लिए **'Create Complaint'** बटन पर क्लिक करें।",
                'en-IN': "You do not have any complaints on record at the moment. If you encounter an issue on campus, click **'Create Complaint'** to report it."
            }
            rep = replies.get(lang, replies['en-IN'])
            return {
                'reply': rep,
                'speak_text': rep,
                'topic': 'my_complaints_empty',
                'language': lang,
                'suggested_actions': ["Create Complaint", "Complaint Status Meanings", "Profile & Settings"]
            }

        counts = summary.get('counts_by_status', {})
        sub = counts.get('submitted', 0)
        prog = counts.get('in_progress', 0)
        rev = counts.get('under_review', 0)
        res = counts.get('resolved', 0)

        lines = [
            f"You have **{total} total complaint(s)** on record (**{active} active**):",
            f"• **Submitted:** `{sub}` | **Under Review:** `{rev}` | **In Progress:** `{prog}` | **Resolved:** `{res}`\n",
            "**Recent Complaints:**"
        ]
        for c in recent:
            icon = "✓" if c.get('is_resolved') else "⏳"
            lines.append(f"• **{c['id']}** — *{c['title']}* [{c['status']}] {icon} (Submitted: {c['submitted_at']})")

        lines.append("\nYou can view full progress or edit details anytime in **'My Complaints'** (`my-complaints.html`).")
        reply_text = "\n".join(lines)
        speak_text = f"You have {total} complaints on record, with {active} currently active. The most recent is {recent[0]['title']} with status {recent[0]['status']}."

        return {
            'reply': reply_text,
            'speak_text': speak_text,
            'topic': 'my_complaints_summary',
            'language': lang,
            'suggested_actions': ["View My Complaints", "Create Complaint", "Help & Support"]
        }

    @classmethod
    def format_notifications_response(cls, notifs: dict, lang: str = 'en-IN') -> dict:
        """
        Formats user notifications summary into rich localized text.
        """
        if not notifs.get('authenticated'):
            return {
                'reply': "Please log in to your account to view your notifications.",
                'speak_text': "Please log in to view your notifications.",
                'topic': 'auth_required',
                'language': lang,
                'suggested_actions': ["Login Page", "Help & Support"]
            }

        unread = notifs.get('unread_count', 0)
        total = notifs.get('total_count', 0)
        recent = notifs.get('recent_notifications', [])

        if total == 0:
            replies = {
                'hi-IN': "आपके पास इस समय कोई नई सूचना (Notification) नहीं है। जब भी आपकी शिकायत पर कोई कार्रवाई होगी, यहाँ अपडेट दिखाई देगा।",
                'en-IN': "You have no notifications on record at the moment. As campus technicians update your complaints, alerts will appear here in real time."
            }
            rep = replies.get(lang, replies['en-IN'])
            return {
                'reply': rep,
                'speak_text': rep,
                'topic': 'notifications_empty',
                'language': lang,
                'suggested_actions': ["View My Complaints", "Create Complaint", "Profile & Settings"]
            }

        lines = [
            f"You have **{unread} unread notification(s)** ({total} total):\n"
        ]
        for n in recent:
            status_tag = "**[NEW]** " if not n.get('is_read') else ""
            lines.append(f"• {status_tag}**{n['title']}** — *{n['message']}* ({n['created_at']})")

        lines.append("\n💡 *Tip:* To delete alerts, open **Notifications Center** (`student-notifications.html`) and click the red **Delete** button.")
        reply_text = "\n".join(lines)
        speak_text = f"You have {unread} unread notifications out of {total} total alerts."

        return {
            'reply': reply_text,
            'speak_text': speak_text,
            'topic': 'notifications_list',
            'language': lang,
            'suggested_actions': ["Open Notifications", "View My Complaints", "Profile & Settings"]
        }

    @classmethod
    def format_profile_response(cls, profile: dict, lang: str = 'en-IN') -> dict:
        """
        Formats user profile information into rich localized text.
        """
        if not profile.get('authenticated'):
            return {
                'reply': "Please log in to view your profile details.",
                'speak_text': "Please log in to view your profile.",
                'topic': 'auth_required',
                'language': lang,
                'suggested_actions': ["Go to Login Page", "Help & Support"]
            }

        lines = [
            f"**Your Verified ProofVoice Profile:**\n",
            f"• **Full Name:** {profile.get('name')}",
            f"• **Role:** {profile.get('role', 'STUDENT').capitalize()}",
            f"• **Institution:** {profile.get('institution') or 'Apex Institute of Technology'}",
            f"• **Email:** `{profile.get('email')}`"
        ]

        if profile.get('student_id'):
            lines.append(f"• **Student ID / Roll No:** `{profile.get('student_id')}`")
        if profile.get('assigned_department'):
            lines.append(f"• **Department:** {profile.get('assigned_department')}")
        if profile.get('semester'):
            lines.append(f"• **Semester / Year:** {profile.get('semester')}")

        lines.append("\n**How to update your profile photo or password:**")
        lines.append("Open **'Profile & Settings'** (`student-profile.html`), click *'Upload Photo'* or fill in *'Change Password'*.")

        reply_text = "\n".join(lines)
        speak_text = f"Your profile is registered as {profile.get('name')} in {profile.get('assigned_department', 'assigned_department')} at {profile.get('institution', 'institution')}."

        return {
            'reply': reply_text,
            'speak_text': speak_text,
            'topic': 'user_profile_info',
            'language': lang,
            'suggested_actions': ["Profile & Settings", "View My Complaints", "Help & Support"]
        }
