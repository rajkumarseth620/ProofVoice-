"""
ProofVoice Intelligent AI Campus Redressal & Help Assistant Service.
Provides context-aware conversational question-answering for:
- ProofVoice registration & multi-institution onboarding
- Student dashboard navigation and metrics
- Voice and text complaint creation & transcription
- Formal grievance application generation & mandatory review
- Complaint lifecycle tracking and status meanings
- Profile editing & credentials persistence
- Personalized notification workflows
- Authenticated, permission-enforced queries about the student's own complaints and account
"""

import re
import logging
from django.db import models
from django.utils import timezone
from apps.complaints.models import Complaint
from apps.accounts.models import User, StudentProfile
from apps.integrations.gnani_service import GnaniAiService

logger = logging.getLogger(__name__)

# Structured Knowledge Base derived from ProofVoice authoritative documentation & FAQs
KNOWLEDGE_TOPICS = [
    {
        'id': 'registration',
        'keywords': ['register', 'registration', 'sign up', 'create account', 'new student', 'unlisted', 'not listed', 'college not in list', 'my institution is not listed', 'enroll'],
        'title': 'Student Registration & Institution Affiliation',
        'response': (
            "**ProofVoice Registration:**\n\n"
            "1. Visit the **Student Registration** page (`/register.html`).\n"
            "2. Select your verified institution from the dropdown list. If your college or university is not listed, choose **\"+ My Institution Is Not Listed\"**.\n"
            "3. Enter your institution name, institution type, city, state, country, and official domain.\n"
            "4. Fill in your academic details (Full Name, Student ID, Department, Year/Semester, and Residential Address).\n"
            "5. ProofVoice will immediately register your student account and grant access to your Student Dashboard. Unlisted institutions are added with `UNVERIFIED` status for separate administrative onboarding."
        )
    },
    {
        'id': 'voice_reporting',
        'keywords': ['voice', 'record', 'microphone', 'mic', 'speech to text', 'stt', 'audio', 'speak', 'transcription', 'transcribe', 'prisma'],
        'title': 'Voice-First Grievance Reporting',
        'response': (
            "**Reporting Issues via Voice:**\n\n"
            "1. Click **\"Report an Issue\"** or **\"Create Complaint\"** in the sidebar.\n"
            "2. Select the **Voice Input** tab and choose your preferred language.\n"
            "3. Tap the **Microphone** button and describe your campus problem naturally.\n"
            "4. Watch the real-time transcription as you speak. When finished, tap **Stop Recording**.\n"
            "5. You can listen to the playback, fix any misheard words in the transcription box, and then click **\"Generate Formal Application\"**.\n"
            "ProofVoice uses Gnani AI Prisma STT with multi-lingual audio processing to accurately transcribe student speech."
        )
    },
    {
        'id': 'review_letter',
        'keywords': ['review', 'formal application', 'letter', 'generate letter', 'confirm', 'mandatory', 'checkbox', 'draft', 'dean letter'],
        'title': 'Mandatory Application Review & Letter Generation',
        'response': (
            "**Formal Application & Mandatory Review:**\n\n"
            "ProofVoice never submits a grievance without your explicit review and confirmation:\n\n"
            "1. After voice or text input, our AI structures your words into a formal institutional grievance letter addressed to the appropriate authority (e.g., Dean of Student Welfare or Department Head).\n"
            "2. The letter automatically incorporates your saved residential address, academic department, and enrollment number.\n"
            "3. You can click **\"Read Aloud\"** to listen to the generated draft via Text-to-Speech.\n"
            "4. You must check the declaration box: *\"I have reviewed this formal application and confirm that the facts, location, and statements are accurate\"* before clicking **\"Submit Authoritative Complaint\"**."
        )
    },
    {
        'id': 'statuses',
        'keywords': ['status', 'statuses', 'tracking', 'mean', 'under review', 'in progress', 'assigned', 'awaiting student', 'resolved', 'rejected', 'reopened'],
        'title': 'Complaint Lifecycle & Status Meanings',
        'response': (
            "**ProofVoice Complaint Statuses:**\n\n"
            "• **Submitted:** Your grievance has been recorded and assigned an authoritative tracking identifier (e.g. `PV-2026-XXXX`).\n"
            "• **Under Review:** Institutional administrators have opened your application and are inspecting the details.\n"
            "• **Assigned:** The ticket has been routed to a specific department (e.g., Estate & Maintenance, IT Services, Hostel Administration) or staff member.\n"
            "• **In Progress:** Technicians or faculty are actively resolving the issue.\n"
            "• **Awaiting Student:** The administration has posted a remark requesting additional photos, details, or confirmation from you.\n"
            "• **Resolved:** The department has completed repairs or resolution and recorded a formal closing remark.\n"
            "• **Reopened:** If the problem recurs or was not adequately fixed, you can reopen the resolved complaint from your dashboard."
        )
    },
    {
        'id': 'profile',
        'keywords': ['profile', 'save profile', 'edit profile', 'photo', 'picture', 'avatar', 'upload photo', 'address', 'student id', 'department', 'semester'],
        'title': 'Student Profile & Credentials Management',
        'response': (
            "**Managing Your Profile & Settings:**\n\n"
            "1. Open **Profile & Settings** (`student-profile.html`) from the sidebar or click your avatar in the top-right header.\n"
            "2. Update your **Full Legal Name**, **Student ID / Roll Number**, **Department / Course**, **Year / Semester**, and **Residential Address**.\n"
            "3. To change your profile picture, click **Upload Photo** (supports JPG, PNG, WebP up to 5MB with automatic cropping and initials fallback).\n"
            "4. Click **\"Save Profile Changes\"** to persist your updates directly into the institutional database.\n"
            "Your saved address and department automatically populate formal letters addressed to the Dean."
        )
    },
    {
        'id': 'notifications',
        'keywords': ['notification', 'notifications', 'alert', 'alerts', 'bell', 'unread', 'mark read', 'email summary', 'in-app'],
        'title': 'Personalized Notification Alerts',
        'response': (
            "**Personalized Notifications:**\n\n"
            "• ProofVoice alerts you only when real events occur on your grievances (submission confirmation, department assignment, admin remarks, request for info, and resolution).\n"
            "• Click the **Notification Bell** in the top navigation bar to see recent alerts, unread counts, or mark all as read.\n"
            "• Click **\"Notifications\"** in the sidebar to open the full Notification Center where you can filter unread alerts and jump directly to ticket details.\n"
            "• You can configure your **In-App Status Alerts** and **Email Summaries** preferences anytime under Profile & Settings."
        )
    },
    {
        'id': 'privacy_isolation',
        'keywords': ['privacy', 'isolation', 'multi tenant', 'security', 'confidential', 'other students', 'safe', 'data'],
        'title': 'Privacy, Security & Multi-Tenant Campus Isolation',
        'response': (
            "**Privacy & Multi-Tenant Isolation:**\n\n"
            "• **Student Isolation:** Students can only view, search, and track their own submitted complaints and notifications.\n"
            "• **Institutional Workspace:** Each college operates in an independent workspace. Administrators from one institution cannot view or manage records from another.\n"
            "• **Confidential Internal Notes:** Administrative discussion notes are strictly protected and never displayed to student accounts.\n"
            "• Passwords are encrypted using PBKDF2 with SHA-256 hashing and API tokens use authenticated token guards."
        )
    },
    {
        'id': 'tts_read_aloud',
        'keywords': ['tts', 'text to speech', 'read aloud', 'audio response', 'listen', 'hear', 'voice output', 'timbre'],
        'title': 'Text-to-Speech & Voice Playback',
        'response': (
            "**Text-to-Speech Accessibility:**\n\n"
            "• On complaint review and details screens, click the **\"Read Aloud\"** button to have your formal application or official admin remarks read aloud.\n"
            "• Inside this AI Help Assistant, toggle **Voice Mode** ON to automatically hear spoken answers to any question.\n"
            "• Use the interactive Audio Player to **Play**, **Pause**, or **Stop** audio anytime.\n"
            "• ProofVoice integrates Gnani AI Timbre TTS with natural Indian English and regional linguistic models."
        )
    }
]

class AiChatService:
    """
    Intelligent chatbot engine for ProofVoice Help & Support.
    Handles text questions, student account status checks, and voice generation.
    """

    @classmethod
    def get_response(cls, message, user=None, history=None, voice_mode=False):
        """
        Processes a user query and returns a structured AI response.
        Enforces authenticated student privacy for account/complaint queries.
        """
        query = (message or '').strip()
        if not query:
            return {
                'reply': "Hello! I am your ProofVoice Campus AI Assistant. How can I assist you with reporting issues, tracking complaints, or navigating your dashboard today?",
                'topic': 'greeting',
                'suggested_actions': [
                    "How do I record a voice complaint?",
                    "Check my complaint status",
                    "How does application review work?",
                    "How do I update my profile?"
                ]
            }

        query_lower = query.lower()

        # Check for conversational greeting
        if re.search(r'^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening))\b', query_lower) and len(query.split()) <= 4:
            student_name = user.full_name if (user and hasattr(user, 'full_name') and user.full_name) else "Student"
            return {
                'reply': f"Hello {student_name}! Welcome to ProofVoice Support. I can help you submit grievances, track your tickets, understand complaint statuses, or update your academic profile. What would you like to know?",
                'topic': 'greeting',
                'suggested_actions': [
                    "What are my active complaints?",
                    "How do I record a voice complaint?",
                    "What does 'Under Review' mean?",
                    "How do notifications work?"
                ]
            }

        # Check for Student Account / Specific Complaint Queries
        account_keywords = ['my complaint', 'my complaints', 'my ticket', 'my status', 'status of my', 'recent complaint', 'active complaint', 'track complaint', 'track my', 'complaint status']
        is_account_query = any(k in query_lower for k in account_keywords)

        # Check if user mentioned a specific complaint ID like "PV-2026-4627" or "PV-AIT-2026-104" or a number
        id_match = re.search(r'\b(PV-[\w\-]+|\b\d{4,6}\b)', query, re.IGNORECASE)

        if (is_account_query or id_match) and user and getattr(user, 'role', '') == 'STUDENT':
            return cls._handle_student_complaints_query(user, query, id_match)

        # Match against Knowledge Base Topics
        best_topic = None
        max_score = 0

        for topic in KNOWLEDGE_TOPICS:
            score = 0
            for kw in topic['keywords']:
                if re.search(r'\b' + re.escape(kw) + r'\b', query_lower):
                    score += 2
                elif kw in query_lower:
                    score += 1

            if score > max_score:
                max_score = score
                best_topic = topic

        if best_topic and max_score >= 2:
            return {
                'reply': best_topic['response'],
                'topic': best_topic['id'],
                'title': best_topic['title'],
                'suggested_actions': cls._get_suggested_actions_for_topic(best_topic['id'])
            }

        # Profile / Account Information queries
        if any(w in query_lower for w in ['who am i', 'my account', 'my email', 'my student id', 'my profile']):
            if user:
                sp = getattr(user, 'student_profile', None)
                inst_name = getattr(user, 'institution_name', '') or (sp.institution.name if sp and sp.institution else 'Institutional Member')
                return {
                    'reply': (
                        f"**Your ProofVoice Account Details:**\n\n"
                        f"• **Name:** {user.full_name or 'N/A'}\n"
                        f"• **Email:** {user.email}\n"
                        f"• **Role:** {user.get_role_display()}\n"
                        f"• **Student ID:** {(sp.student_id if sp else None) or 'Not set'}\n"
                        f"• **Department:** {(sp.department if sp else None) or 'Not set'}\n"
                        f"• **Institution:** {inst_name}\n\n"
                        f"You can edit and update these credentials on the **Profile & Settings** page."
                    ),
                    'topic': 'profile',
                    'suggested_actions': ["Edit My Profile", "What are my complaints?", "How do I report an issue?"]
                }

        # Fallback for unrecognized questions
        return {
            'reply': (
                "I don't have that specific information in the ProofVoice support knowledge base. "
                "ProofVoice is designed specifically for reporting campus grievances, preparing formal applications, and tracking institutional resolution.\n\n"
                "If this is related to institutional academic grading, fee refunds, or policy questions outside of campus grievances, "
                "please contact your university's **Dean of Student Welfare** or **Campus Grievance Redressal Committee** directly."
            ),
            'topic': 'unrecognized',
            'suggested_actions': [
                "How do I record a complaint?",
                "What do complaint statuses mean?",
                "How do I update my profile?",
                "What are my active complaints?"
            ]
        }

    @classmethod
    def _handle_student_complaints_query(cls, student_user, query, id_match):
        """
        Queries live MySQL database for the authenticated student's complaints.
        Strictly enforces permissions and privacy boundaries.
        """
        # If user asked for a specific ID
        if id_match:
            candidate_id = id_match.group(1).strip()
            complaint = Complaint.objects.filter(student=student_user).filter(
                models.Q(complaint_id__iexact=candidate_id) | models.Q(id__iexact=candidate_id)
            ).first()

            if not complaint:
                # Check if this complaint ID exists for another student
                other_exists = Complaint.objects.filter(
                    models.Q(complaint_id__iexact=candidate_id) | models.Q(id__iexact=candidate_id)
                ).exists()
                if other_exists:
                    return {
                        'reply': (
                            f"I cannot access complaint `{candidate_id}` from your account. "
                            f"For student privacy and security, you can only view complaints submitted by your own account."
                        ),
                        'topic': 'complaint_privacy_forbidden'
                    }
                else:
                    return {
                        'reply': (
                            f"I could not find any complaint matching identifier `{candidate_id}` in your account records. "
                            f"Please check your tracking ID on the **My Complaints** page."
                        ),
                        'topic': 'complaint_not_found',
                        'suggested_actions': ["View My Complaints", "Report an Issue"]
                    }

            dept_name = complaint.assigned_department.name if complaint.assigned_department else "Not assigned yet"
            last_history = complaint.status_history.order_by('-timestamp').first()
            remark = last_history.public_remark if last_history and last_history.public_remark else "No public remark recorded."

            return {
                'reply': (
                    f"**Complaint Details for `{complaint.complaint_id}`:**\n\n"
                    f"• **Title:** {complaint.title}\n"
                    f"• **Current Status:** **{complaint.get_status_display()}**\n"
                    f"• **Category:** {complaint.category or 'General'}\n"
                    f"• **Assigned Department:** {dept_name}\n"
                    f"• **Location:** {complaint.full_issue_location or complaint.building or 'Campus'}\n"
                    f"• **Submitted On:** {complaint.submission_timestamp.strftime('%B %d, %Y at %I:%M %p') if complaint.submission_timestamp else 'Recently'}\n"
                    f"• **Latest Remark:** {remark}\n\n"
                    f"You can view the full timeline and letter on the [Complaint Details page](complaint-details.html?id={complaint.complaint_id})."
                ),
                'topic': 'complaint_single_status',
                'complaint_id': complaint.complaint_id,
                'suggested_actions': [
                    f"View {complaint.complaint_id} Details",
                    "Check all my complaints",
                    "How do I file a new complaint?"
                ]
            }

        # Otherwise list student's recent complaints
        complaints = Complaint.objects.filter(student=student_user).order_by('-submission_timestamp', '-created_at')[:5]
        total_count = Complaint.objects.filter(student=student_user).count()

        if total_count == 0:
            return {
                'reply': (
                    "You have not submitted any complaints yet. "
                    "Whenever you encounter a problem with campus facilities, washrooms, classrooms, or hostel rooms, "
                    "you can click **\"Report an Issue\"** to speak or type your grievance."
                ),
                'topic': 'no_complaints',
                'suggested_actions': ["Report an Issue with Voice", "How does voice reporting work?"]
            }

        lines = [f"You have **{total_count}** complaint{'s' if total_count != 1 else ''} on record. Here are your most recent:"]
        for c in complaints:
            status_emoji = "✓" if c.status == Complaint.Status.RESOLVED else "⏳"
            lines.append(f"• **{c.complaint_id}** — *{c.title}* [{c.get_status_display()}] {status_emoji}")

        lines.append("\nYou can ask me for details about any of these tickets (e.g. *\"Status of " + complaints[0].complaint_id + "\"*) or click **My Complaints** in the sidebar to review all tickets.")

        return {
            'reply': "\n".join(lines),
            'topic': 'complaints_summary',
            'suggested_actions': [
                f"Status of {complaints[0].complaint_id}",
                "View My Complaints",
                "Create a new complaint"
            ]
        }

    @classmethod
    def _get_suggested_actions_for_topic(cls, topic_id):
        if topic_id == 'voice_reporting':
            return ["Can I edit my transcription?", "How do I review before submitting?", "Report an Issue Now"]
        elif topic_id == 'review_letter':
            return ["Why is review mandatory?", "What do statuses mean?", "How do I listen aloud?"]
        elif topic_id == 'statuses':
            return ["What does 'Under Review' mean?", "What are my active complaints?", "Can I reopen a complaint?"]
        elif topic_id == 'profile':
            return ["Where do I upload a photo?", "What are my notifications?", "Open Profile Settings"]
        elif topic_id == 'notifications':
            return ["How do I mark alerts as read?", "Configure notification preferences", "Open Notification Center"]
        elif topic_id == 'registration':
            return ["How do I select an unlisted college?", "Login to Dashboard", "How do I report an issue?"]
        return [
            "How do I record a complaint?",
            "What are my active complaints?",
            "What do statuses mean?"
        ]
