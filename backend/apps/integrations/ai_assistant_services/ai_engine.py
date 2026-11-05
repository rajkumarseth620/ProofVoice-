# -*- coding: utf-8 -*-
"""
ProofVoice Advanced Multi-Turn Conversational AI Reasoning Engine.
Coordinates:
1. Intent Classification:
   - GENERAL_KNOWLEDGE: Direct AI educational answers (never triggers complaints).
   - WEBSITE_SUPPORT: Verified ProofVoice website guidance.
   - CAMPUS_COMPLAINT: Activated only when reporting issues or tracking tickets.
2. Primary reasoning: OpenAI API (gpt-4o-mini / gpt-4o) with multi-turn conversation memory.
3. Secondary reasoning: Google Gemini API (gemini-1.5-flash).
4. Web search integration: DuckDuckGo / Wikipedia / Serper live retrieval.
5. Built-in General Knowledge Base: Instant, comprehensive educational explanations.
6. Campus Knowledge Base: Verified ProofVoice workflows.
"""
import os
import re
import json
import logging
import requests
from django.conf import settings

from .language_detection import SUPPORTED_LANGUAGES, detect_language, normalize_text
from .intent_classifier import IntentClassifier, AssistantIntent
from .campus_knowledge import match_campus_knowledge
from .general_knowledge import match_general_knowledge
from .web_search import WebSearchService
from .conversation_memory import ConversationMemory
from .user_context import UserContextService

logger = logging.getLogger(__name__)

STRICT_SYSTEM_INSTRUCTION = (
    "You are ProofVoice AI, an intelligent, multilingual, general-purpose conversational assistant integrated into the ProofVoice website.\n\n"
    "You are capable of answering general questions across virtually all subjects, including education, computer science, programming, mathematics, science, technology, history, geography, business, current affairs and everyday life.\n\n"
    "You are also an expert guide for the ProofVoice website.\n\n"
    "You have three responsibilities:\n"
    "1. Answer general questions intelligently, accurately and naturally.\n"
    "2. Help users understand and operate the actual ProofVoice website.\n"
    "3. Assist users with campus complaints when they explicitly request complaint-related assistance.\n\n"
    "Never assume that a question is a complaint merely because it mentions computers, networks, Wi-Fi, laboratories, classrooms or equipment.\n\n"
    "Understand the user's actual intention before selecting an action.\n\n"
    "For general questions, answer directly without showing complaint categories, departments, priorities or complaint submission instructions.\n\n"
    "For website-related questions, provide accurate instructions based on the actual ProofVoice implementation.\n\n"
    "For complaint-related requests, use the existing authorized complaint workflow.\n\n"
    "Maintain conversation context.\n\n"
    "Respond in the language used by the user unless another language is requested.\n\n"
    "Never fabricate information.\n\n"
    "Never claim to have completed an action without verifying it."
)


class AiEngineService:

    @classmethod
    def get_system_instruction(cls, user_summary: dict, lang: str, web_context: str = "") -> str:
        lang_meta = SUPPORTED_LANGUAGES.get(lang, {'name': 'English', 'native': 'English'})
        lang_name = lang_meta.get('name', 'English')

        user_info = ""
        if user_summary.get('authenticated'):
            user_info = (
                f"- Name: {user_summary.get('name')}\n"
                f"- Role: {user_summary.get('role')}\n"
                f"- Institution: {user_summary.get('institution')}\n"
                f"- Active Complaints Count: {user_summary.get('complaints_count')}\n"
            )
            if user_summary.get('active_complaints'):
                recent_c = user_summary.get('active_complaints')[0]
                user_info += f"- Most Recent Ticket: {recent_c['id']} ({recent_c['title']} - Status: {recent_c['status']})\n"
        else:
            user_info = "- Authentication: Guest / Student not logged in\n"

        prompt = (
            f"{STRICT_SYSTEM_INSTRUCTION}\n\n"
            f"USER CONTEXT:\n{user_info}"
            f"- Preferred Response Language: {lang_name} ({lang})\n\n"
            f"PROOFVOICE WEBSITE CAPABILITIES & PROCEDURES:\n"
            f"• Sign Out: Red button '[-> Sign Out' near the bottom of the left sidebar above the profile card. Clears session and redirects to login.html.\n"
            f"• Student Registration: In register.html, select institution (or '+ My Institution Is Not Listed'), fill Legal Name, Institutional Email, Department, Year/Semester, Student ID, Residential Address, and Password.\n"
            f"• Student Login: In login.html, enter email and password. Case-sensitive credentials.\n"
            f"• Create Complaint: In new-complaint.html (or '+ New Complaint'), choose category, room/lab location, type or speak via Gnani AI Prisma speech-to-text. Generates an official formal application letter.\n"
            f"• My Complaints & Status Tracking: In my-complaints.html, track submitted tickets. Statuses: Submitted (Yellow) -> Under Review (Blue) -> In Progress (Teal) -> Resolved (Green) -> Escalated (Red).\n"
            f"• Edit Complaint: In complaint-details.html, click 'Edit Application' to update details before resolution.\n"
            f"• Delete Complaint: In complaint-details.html, click 'Delete Application' to withdraw the complaint.\n"
            f"• Profile & Photo Upload: In student-profile.html, click 'Upload Photo' under Profile Picture (supports JPG, PNG, WebP up to 5MB), preview live, click 'Save Photo'. Update legal name, department, address, click 'Save Profile Changes'.\n"
            f"• Password Management: In student-profile.html, scroll to 'Change Password', type current password and new password (min 8 chars), click 'Update Password'.\n"
            f"• Notifications: In student-notifications.html, delete individual alerts using the red 'Delete' button or clear all via 'Clear All'."
        )

        if web_context:
            prompt += f"\n\nVERIFIED INTERNET SEARCH DATA:\n{web_context}\nUse this verified real-time information to answer accurately."

        return prompt

    @classmethod
    def generate_response(cls, query: str, user=None, history=None, preferred_language: str = 'en-IN') -> dict:
        raw_query = (query or '').strip()
        lang = detect_language(raw_query, preferred_language)
        user_summary = UserContextService.get_user_summary(user)
        last_subject = ConversationMemory.get_last_assistant_topic(history)

        # ----------------------------------------------------------------------
        # 1. INTENT CLASSIFICATION
        # ----------------------------------------------------------------------
        intent = IntentClassifier.classify(raw_query, lang)

        # ----------------------------------------------------------------------
        # AMBIGUOUS / CLARIFICATION CHECK
        # ----------------------------------------------------------------------
        clean_q = raw_query.lower().strip('?!., ')
        ambiguous_terms = [
            'help', 'madad', 'sahayata', 'kya', 'problem', 'samayasa', 'shikayat', 'complaint', 'status', 'kaise', 'batao',
            'hi', 'hello', 'hey', 'namaste', 'namaskar',
            'मदद', 'सहायता', 'नमस्ते', 'नमस्कार', 'प्रणाम', 'शिकायत', 'समस्या', 'स्टेटस', 'क्या', 'कैसे', 'बताओ'
        ]
        greetings_terms = [
            'hi', 'hello', 'hey', 'namaste', 'namaskar', 'pranam', 'नमस्ते', 'नमस्कार', 'प्रणाम'
        ]
        if clean_q in ambiguous_terms:
            if clean_q in greetings_terms:
                student_name = user_summary.get('name') or ('Student' if lang == 'en-IN' else 'छात्र')
                if lang == 'hi-IN':
                    return {
                        'reply': f"नमस्ते {student_name}! ProofVoice कैंपस सहायता में आपका स्वागत है। आप शिकायत दर्ज करने, स्टेटस जांचने, प्रोफाइल अपडेट करने या परिसर से संबंधित कोई भी सवाल पूछ सकते हैं। आप क्या जानना चाहते हैं?",
                        'speak_text': f"नमस्ते {student_name}! ProofVoice सहायता में आपका स्वागत है। मैं आपकी क्या मदद कर सकता हूँ?",
                        'topic': 'greeting',
                        'language': 'hi-IN',
                        'suggested_actions': ["बोलकर शिकायत कैसे दर्ज करें?", "मेरी सक्रिय शिकायतें दिखाओ", "प्रोफाइल कैसे अपडेट करें?", "स्टेटस का अर्थ"]
                    }
                else:
                    return {
                        'reply': f"Hello {student_name}! Welcome to ProofVoice Campus Support. I can help you lodge grievances, check resolution timelines, update your profile, or answer questions about campus rules. How can I assist you today?",
                        'speak_text': f"Hello {student_name}! Welcome to ProofVoice Support. How can I assist you today?",
                        'topic': 'greeting',
                        'language': 'en-IN',
                        'suggested_actions': ["How do I file a complaint?", "What are my active complaints?", "Update my profile", "Complaint status meanings"]
                    }

            # Generic single-word inquiry clarification
            if lang == 'hi-IN':
                return {
                    'reply': (
                        "मैं आपकी पूरी सहायता के लिए तैयार हूँ! कृपया बताएं कि आप क्या करना चाहते हैं:\n\n"
                        "1. **नई शिकायत दर्ज करना:** क्लासरूम, लैब, हॉस्टल, बिजली, पानी या इंटरनेट समस्या की रिपोर्ट।\n"
                        "2. **सक्रिय शिकायतों का स्टेटस:** अपने दर्ज किए गए टिकटों की प्रगति और तकनीशियन टिप्पणी देखना।\n"
                        "3. **पोर्टल उपयोग मार्गदर्शन:** रजिस्ट्रेशन, पासवर्ड बदलना, प्रोफाइल फोटो लगाना या साइन आउट।\n"
                        "4. **अकादमिक व सामान्य प्रश्न:** परिसर से संबंधित किसी भी विषय पर जानकारी।"
                    ),
                    'speak_text': "कृपया स्पष्ट करें कि आप क्या करना चाहते हैं। आप नई शिकायत दर्ज कर सकते हैं या स्टेटस देख सकते हैं।",
                    'topic': 'clarification_needed',
                    'language': 'hi-IN',
                    'suggested_actions': ["शिकायत दर्ज करें", "मेरी शिकायतें दिखाओ", "प्रोफाइल सेटिंग्स", "स्टेटस का अर्थ"]
                }
            else:
                return {
                    'reply': (
                        "I am here to help! Could you please clarify what specific assistance you need?\n\n"
                        "1. **File a Campus Grievance:** Report classroom equipment, Wi-Fi, electricity, sanitation, or hostel issues.\n"
                        "2. **Track Active Complaints:** Review progress milestones and technician remarks on your tickets.\n"
                        "3. **Platform Guidance:** Steps for registration, photo upload, password changes, or signing out.\n"
                        "4. **General & Academic Inquiries:** Ask any question regarding campus rules, facilities, or studies."
                    ),
                    'speak_text': "How can I help you today? You can report an issue, track existing complaints, or get website assistance.",
                    'topic': 'clarification_needed',
                    'language': 'en-IN',
                    'suggested_actions': ["Report an Issue", "Check My Complaints", "Profile & Settings", "Status Meanings"]
                }

        # ----------------------------------------------------------------------
        # MULTI-TURN CONTEXT & FOLLOW-UP RESOLUTION
        # ----------------------------------------------------------------------
        if re.search(r'\b(is\s*it\s*free|is\s*proofvoice\s*free|kya\s*ye\s*free\s*hai|fees\s*lagti\s*hai)\b', raw_query, re.IGNORECASE):
            if lang == 'hi-IN':
                return {
                    'reply': "**हाँ, ProofVoice पूरी तरह निःशुल्क है!** परिसर के सभी सत्यापित छात्रों के लिए शिकायत दर्ज करना, स्टेटस ट्रैक करना, और AI सहायता प्राप्त करना पूरी तरह मुफ्त है। इसके लिए कोई शुल्क नहीं लिया जाता।",
                    'speak_text': "हाँ, ProofVoice सभी सत्यापित छात्रों के लिए पूरी तरह निःशुल्क है।",
                    'topic': 'service_pricing_free',
                    'language': 'hi-IN',
                    'suggested_actions': ["शिकायत दर्ज करें", "मेरी शिकायतें", "सहायता और सपोर्ट"]
                }
            else:
                return {
                    'reply': "**Yes, ProofVoice is 100% free for all students!** There are no fees or hidden charges for reporting campus issues, generating formal grievance letters, tracking resolution, or using the AI Assistant.",
                    'speak_text': "Yes, ProofVoice is completely free for all campus students.",
                    'topic': 'service_pricing_free',
                    'language': 'en-IN',
                    'suggested_actions': ["Create Complaint", "My Complaints", "Help & Support"]
                }

        # Follow-up "Tell me more" / "Aur batao"
        if re.search(r'\b(tell\s*me\s*more|explain\s*more|aur\s*batao|aur\s*samjhao|aur\s*kya|what\s*next)\b', raw_query, re.IGNORECASE):
            if last_subject:
                if 'complaint' in last_subject.lower() or 'grievance' in last_subject.lower() or 'status' in last_subject.lower():
                    if lang == 'hi-IN':
                        return {
                            'reply': (
                                "**शिकायत प्रक्रिया के अगले चरण:**\n\n"
                                "1. शिकायत दर्ज होने के बाद आपके संबंधित विभाग (जैसे Estate, IT, Hostel) को तुरंत सूचना भेजी जाती है。\n"
                                "2. अधिकारी **Under Review** स्थिति में समस्या का निरीक्षण करते हैं और तकनीशियन नियुक्त करते हैं。\n"
                                "3. तकनीशियन द्वारा मरम्मत पूरी करने पर शिकायत **Resolved** के रूप में बंद कर दी जाती है。\n"
                                "4. यदि आप संतुष्ट न हों, तो आप टिकट को पुनः खोल (Reopen) भी सकते हैं।"
                            ),
                            'speak_text': "शिकायत दर्ज होने के बाद संबंधित विभाग निरीक्षण करता है, तकनीशियन नियुक्त करता है और मरम्मत पूरी करता है।",
                            'topic': 'followup_complaint_lifecycle',
                            'language': 'hi-IN',
                            'suggested_actions': ["मेरी सक्रिय शिकायतें", "नई शिकायत दर्ज करें", "सहायता"]
                        }
                    else:
                        return {
                            'reply': (
                                "**Next Steps in the Grievance Lifecycle:**\n\n"
                                "1. Once submitted, your grievance is dispatched to the relevant department (Estate, IT, Hostel, or Academic).\n"
                                "2. Administrators review the letter under **'Under Review'** and assign a qualified campus technician.\n"
                                "3. The technician inspects the site, updates the status to **'In Progress'**, and logs public progress remarks.\n"
                                "4. Upon verified repair, the ticket is marked **'Resolved'**. If the issue recurs, you can reopen it directly."
                            ),
                            'speak_text': "After submission, administrators inspect your application, dispatch a technician, and resolve the issue.",
                            'topic': 'followup_complaint_lifecycle',
                            'language': 'en-IN',
                            'suggested_actions': ["Check My Complaints", "Create New Complaint", "Help & Support"]
                        }

        # ----------------------------------------------------------------------
        # INTENT B: WEBSITE_SUPPORT
        # ----------------------------------------------------------------------
        if intent == AssistantIntent.WEBSITE_SUPPORT:
            campus_res = match_campus_knowledge(raw_query, lang)
            if campus_res:
                return campus_res

        # ----------------------------------------------------------------------
        # AUTHENTICATED DATABASE QUERIES (COMPLAINTS, NOTIFICATIONS, PROFILE)
        # ----------------------------------------------------------------------
        from .campus_database import CampusDatabaseService

        # Notifications Query
        if re.search(r'\b(my\s*notifications?|show\s*(my\s*)?notifications?|check\s*(my\s*)?notifications?|do\s*i\s*have\s*(any\s*)?notifications?|unread\s*notifications?)\b', raw_query, re.IGNORECASE) or \
           re.search(r'(सूचनाएं|नोटिफिकेशन|अलर्ट)', raw_query):
            n_sum = CampusDatabaseService.get_user_notifications_summary(user)
            return CampusDatabaseService.format_notifications_response(n_sum, lang)

        # Profile Information Query
        if re.search(r'\b(my\s*profile(\s*info)?|who\s*am\s*i|my\s*student\s*id|my\s*roll\s*no|what\s*is\s*my\s*name|my\s*department)\b', raw_query, re.IGNORECASE) or \
           re.search(r'(मेरी\s*प्रोफाइल|मेरा\s*नाम|मेरी\s*आईडी)', raw_query):
            p_sum = CampusDatabaseService.get_user_profile_summary(user)
            return CampusDatabaseService.format_profile_response(p_sum, lang)

        # Complaints Summary Query
        if re.search(r'\b(my\s*(active\s*)?complaints?|status\s*of\s*my|check\s*my\s*(active\s*)?complaints?|show\s*my\s*complaints?|how\s*many\s*(active\s*)?complaints|last\s*complaint|latest\s*complaint)\b', raw_query, re.IGNORECASE) or \
           re.search(r'(मेरी\s*सक्रिय\s*शिकायतें|मेरी\s*शिकायतें\s*दिखाओ|मेरी\s*शिकायत|शिकायत\s*का\s*स्टेटस)', raw_query):
            c_sum = CampusDatabaseService.get_user_complaints_summary(user)
            return CampusDatabaseService.format_complaints_response(c_sum, lang)

        # ----------------------------------------------------------------------
        # INTENT C: CAMPUS_COMPLAINT
        # Activated ONLY when explicitly reporting a problem or tracking tickets
        # ----------------------------------------------------------------------
        if intent == AssistantIntent.CAMPUS_COMPLAINT:
            # Check if user is asking to track their complaints
            if re.search(r'\b(my\s*(active\s*)?complaints?|status\s*of\s*my|check\s*my\s*(active\s*)?complaints?|show\s*my\s*complaints?)\b', raw_query, re.IGNORECASE) or \
               re.search(r'(मेरी\s*सक्रिय\s*शिकायतें|मेरी\s*शिकायतें\s*दिखाओ|मेरी\s*शिकायत|शिकायत\s*का\s*स्टेटस)', raw_query):
                if user_summary.get('authenticated'):
                    active = user_summary.get('active_complaints', [])
                    if not active:
                        reply = "You do not have any active complaints on record at the moment. If you encounter an issue on campus, you can file a new complaint using the **'Create Complaint'** button."
                        return {
                            'reply': reply,
                            'speak_text': "You have no active complaints on record. Click Create Complaint to report an issue.",
                            'topic': 'personal_complaints_empty',
                            'language': lang,
                            'suggested_actions': ["Create Complaint", "How does voice recording work?", "Profile & Settings"]
                        }
                    lines = [f"You have **{len(active)} active complaint(s)** on record:"]
                    for c in active[:5]:
                        lines.append(f"• **{c['id']}** — *{c['title']}* [**Status: {c['status']}**]")
                    lines.append("\nYou can track full progress or update details in **My Complaints** (`my-complaints.html`).")
                    return {
                        'reply': "\n".join(lines),
                        'speak_text': f"You have {len(active)} active complaints. The most recent is {active[0]['title']} with status {active[0]['status']}.",
                        'topic': 'personal_complaints_list',
                        'language': lang,
                        'suggested_actions': ["View My Complaints", "Create Complaint", "Help & Support"]
                    }
                else:
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

            # If user describes an issue requiring complaint assistance
            # Example: "My classroom projector is broken. I want to report it."
            from apps.integrations.ai_assistant import DEPARTMENT_CATEGORY_RULES
            matched_dept = "Campus IT Services"
            matched_cat = "Classroom and Laboratory"
            matched_prio = "HIGH"
            item_name = "Classroom Equipment"

            q_lower = raw_query.lower()
            if re.search(r'\b(projector|screen|smartboard|chair|bench|desk|lab)\b', q_lower) or re.search(r'(प्रोजेक्टर|कुर्सी|बेंच|डेस्क|लैब|क्लास)', raw_query):
                matched_dept = "Campus IT & Facilities Services"
                matched_cat = "Classroom and Laboratory"
                matched_prio = "HIGH"
                item_name = "कक्षा एवं लैब उपकरण" if lang == 'hi-IN' else "Classroom & Lab Equipment"
            elif re.search(r'\b(fan|light|ac|electricity|power|bulb)\b', q_lower) or re.search(r'(बिजली|पंखा|लाइट|करंट|वायर|बल्ब)', raw_query):
                matched_dept = "Electrical Maintenance Division"
                matched_cat = "Electricity and Lighting"
                matched_prio = "HIGH"
                item_name = "विद्युत उपकरण एवं लाइटिंग" if lang == 'hi-IN' else "Electrical Appliance & Lighting"
            elif re.search(r'\b(water|tap|toilet|washroom|sanitation|leak)\b', q_lower) or re.search(r'(पानी|नल|शौचालय|वॉशरूम|टॉयलेट|स्वच्छता|लीक)', raw_query):
                matched_dept = "Estate and Sanitation Office"
                matched_cat = "Water and Sanitation"
                matched_prio = "HIGH"
                item_name = "जल आपूर्ति एवं स्वच्छता" if lang == 'hi-IN' else "Water Supply & Sanitation"
            elif re.search(r'\b(wifi|wi-fi|internet|lan|network)\b', q_lower) or re.search(r'(इंटरनेट|वाईफाई|वाई-फाई|कंप्यूटर|सर्वर|नेटवर्क)', raw_query):
                matched_dept = "Campus IT & Network Services"
                matched_cat = "IT Services & Network"
                matched_prio = "URGENT"
                item_name = "कैंपस इंटरनेट एवं वाई-फाई" if lang == 'hi-IN' else "Campus Internet & Wi-Fi"
            elif re.search(r'\b(hostel|mess|food|warden)\b', q_lower) or re.search(r'(हॉस्टल|छात्रावास|मेस|खाना|वॉर्डन)', raw_query):
                matched_dept = "Hostel Administration Office"
                matched_cat = "Hostel and Accommodation"
                matched_prio = "MEDIUM"
                item_name = "छात्रावास (हॉस्टल) सुविधा" if lang == 'hi-IN' else "Hostel Facility"

            if lang == 'hi-IN':
                dept_hi_map = {
                    "Campus IT & Facilities Services": "कैंपस आईटी और सुविधाएं विभाग",
                    "Electrical Maintenance Division": "विद्युत रखरखाव प्रभाग",
                    "Estate and Sanitation Office": "संपत्ति एवं स्वच्छता कार्यालय",
                    "Campus IT & Network Services": "कैंपस आईटी और नेटवर्क सेवाएं",
                    "Hostel Administration Office": "छात्रावास प्रशासन कार्यालय"
                }
                cat_hi_map = {
                    "Classroom and Laboratory": "क्लासरूम और प्रयोगशाला",
                    "Electricity and Lighting": "बिजली और लाइटिंग",
                    "Water and Sanitation": "जल आपूर्ति और स्वच्छता",
                    "IT Services & Network": "आईटी सेवाएं और नेटवर्क",
                    "Hostel and Accommodation": "छात्रावास (हॉस्टल) और आवास"
                }
                complaint_reply = (
                    f"मैं समझता हूँ कि आपको **{item_name}** से संबंधित समस्या आ रही है और आप इसकी शिकायत दर्ज करना चाहते हैं। 🛠️\n\n"
                    f"• **अनुशंसित श्रेणी:** `{cat_hi_map.get(matched_cat, matched_cat)}`\n"
                    f"• **संबंधित विभाग:** **{dept_hi_map.get(matched_dept, matched_dept)}**\n"
                    f"• **सुझाई गई प्राथमिकता:** `{matched_prio}`\n\n"
                    f"**शिकायत दर्ज करने की प्रक्रिया:**\n"
                    f"1. साइडबार में **'+ New Complaint'** (`new-complaint.html`) पर क्लिक करें।\n"
                    f"2. श्रेणी में **{cat_hi_map.get(matched_cat, matched_cat)}** चुनें और अपना कमरा या ब्लॉक नंबर दर्ज करें।\n"
                    f"3. समस्या को बोलकर (माइक बटन दबाकर) या लिखकर दर्ज करें। ProofVoice आपके लिए औपचारिक आवेदन पत्र तैयार कर देगा।\n"
                    f"4. पत्र की जांच करें और **'Submit Grievance'** पर क्लिक करें।"
                )
                speak_text = f"मैं समझता हूँ कि आपको {item_name} की समस्या है। आप New Complaint पेज पर जाकर शिकायत दर्ज कर सकते हैं।"
                suggested_actions = ["शिकायत दर्ज करें", "वॉइस रिपोर्टिंग कैसे काम करती है?", "मेरी शिकायतें"]
            else:
                complaint_reply = (
                    f"I understand you are experiencing an issue with your **{item_name}** and would like to report it! 🛠️\n\n"
                    f"• **Recommended Category:** `{matched_cat}`\n"
                    f"• **Assigned Department:** **{matched_dept}**\n"
                    f"• **Suggested Priority:** `{matched_prio}`\n\n"
                    f"**How to Lodge This Complaint Now:**\n"
                    f"1. Click on **'Create Complaint'** (`new-complaint.html`) in your sidebar or top button.\n"
                    f"2. Select Category **{matched_cat}** and specify your classroom or room number.\n"
                    f"3. Type or tap the microphone to speak your issue in your language. ProofVoice will generate a formal institutional grievance letter.\n"
                    f"4. Review and click **Submit Grievance** for swift campus resolution."
                )
                speak_text = f"I understand you want to report an issue with {item_name}. You can submit this under {matched_cat} to {matched_dept}."
                suggested_actions = ["Create Complaint Now", "How does voice reporting work?", "My Complaints"]

            return {
                'intent': 'CAMPUS_COMPLAINT',
                'reply': complaint_reply,
                'speak_text': speak_text,
                'topic': 'campus_complaint_workflow',
                'language': lang,
                'suggested_actions': suggested_actions
            }

        # ----------------------------------------------------------------------
        # INTENT A: GENERAL_KNOWLEDGE
        # For education, programming, science, technology, world facts, and smalltalk
        # NEVER show complaint classifications or departments!
        # ----------------------------------------------------------------------

        # Step 2a: Check Built-in General Knowledge Base (Instant, verified answers)
        gk_res = match_general_knowledge(raw_query, lang, last_subject)
        if gk_res:
            return gk_res

        # Step 2b: Check Web Search if external information is needed
        web_context = ""
        web_sources = []
        if WebSearchService.should_search_web(raw_query):
            search_res = WebSearchService.search(raw_query)
            if search_res.get('success'):
                web_context = search_res.get('summary', '')
                web_sources = search_res.get('sources', [])

        system_instruction = cls.get_system_instruction(user_summary, lang, web_context)

        # Step 2c: Primary Reasoning Engine: OpenAI API (gpt-4o-mini / gpt-4o)
        openai_key = (
            getattr(settings, 'OPENAI_API_KEY', '') or
            os.getenv('OPENAI_API_KEY', '')
        ).strip()

        if openai_key:
            try:
                from .openai_engine import OpenAiEngine
                messages = ConversationMemory.format_history_for_openai(history, system_instruction, raw_query)
                model_name = getattr(settings, 'OPENAI_MODEL', '') or os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
                res = OpenAiEngine.generate_chat_completion(messages, model=model_name, temperature=0.7, max_tokens=850)
                if res.get('success'):
                    reply = res.get('content', '').strip()
                    if web_sources:
                        reply += "\n\n**Sources:**\n" + "\n".join([f"- [{s.get('title')}]({s.get('url')})" for s in web_sources])
                    speak = re.sub(r'[*#_`•✓⏳\n]+', ' ', reply).strip()
                    return {
                        'reply': reply,
                        'speak_text': speak[:300],
                        'language': lang,
                        'topic': 'openai_general_reasoning',
                        'sources': web_sources,
                        'suggested_actions': ["Explain more", "Ask another question", "Help & Support"]
                    }
                else:
                    logger.warning(f"OpenAI completion issue: {res.get('error')}")
            except Exception as e:
                logger.warning(f"OpenAI API call failed: {e}")

        # Step 2d: Secondary Reasoning Engine: Google Gemini API
        gemini_key = (
            getattr(settings, 'GEMINI_API_KEY', '') or
            os.getenv('GEMINI_API_KEY', '') or
            os.getenv('GOOGLE_API_KEY', '')
        ).strip()

        if gemini_key:
            try:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                prompt_text = f"{system_instruction}\n\nStudent Query: {raw_query}"
                res = requests.post(
                    endpoint,
                    json={
                        "contents": [{"role": "user", "parts": [{"text": prompt_text}]}],
                        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 850}
                    },
                    timeout=10
                )
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get('candidates', [])
                    if candidates and 'content' in candidates[0]:
                        parts = candidates[0]['content'].get('parts', [])
                        if parts and 'text' in parts[0]:
                            reply = parts[0]['text'].strip()
                            if web_sources:
                                reply += "\n\n**Sources:**\n" + "\n".join([f"- [{s.get('title')}]({s.get('url')})" for s in web_sources])
                            speak = re.sub(r'[*#_`•✓⏳\n]+', ' ', reply).strip()
                            return {
                                'reply': reply,
                                'speak_text': speak[:300],
                                'language': lang,
                                'topic': 'gemini_general_reasoning',
                                'sources': web_sources,
                                'suggested_actions': ["Explain more", "Ask another question", "Help & Support"]
                            }
            except Exception as e:
                logger.warning(f"Gemini API call failed: {e}")

        # Step 2e: Web Search Direct Answer (if retrieved from internet)
        if web_context:
            sources_md = "\n".join([f"- [{s.get('title')}]({s.get('url')})" for s in web_sources])
            reply = f"{web_context}\n\n**Sources & Reference:**\n{sources_md}"
            speak = re.sub(r'[*#_`•✓⏳\n]+', ' ', web_context).strip()
            return {
                'reply': reply,
                'speak_text': speak[:300],
                'language': lang,
                'topic': 'web_search_direct',
                'sources': web_sources,
                'suggested_actions': ["Tell me more", "Ask another question", "Help & Support"]
            }

        # Step 2f: Dynamic Educational Knowledge Synthesizer
        # For general, educational, and technical questions, synthesize a comprehensive explanation
        # rather than returning an unhelpful generic delay message.
        from .general_knowledge import generate_dynamic_educational_explanation
        return generate_dynamic_educational_explanation(raw_query, lang)
