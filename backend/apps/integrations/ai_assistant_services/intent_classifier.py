# -*- coding: utf-8 -*-
"""
ProofVoice Advanced AI Assistant Intent Classifier (English & Hindi).
Categorizes incoming queries into 3 mutually exclusive intents:
1. GENERAL_KNOWLEDGE: Questions across all subjects, education, science, math, technology, everyday life.
2. WEBSITE_SUPPORT: Specific procedural guidance for operating ProofVoice.
3. CAMPUS_COMPLAINT: Activated ONLY when reporting or tracking grievances.
"""

import re
from enum import Enum

class AssistantIntent(str, Enum):
    GENERAL_KNOWLEDGE = 'GENERAL_KNOWLEDGE'
    WEBSITE_SUPPORT = 'WEBSITE_SUPPORT'
    CAMPUS_COMPLAINT = 'CAMPUS_COMPLAINT'


# Active defect or problem indicators that demonstrate an actual grievance
CAMPUS_DEFECT_INDICATORS = [
    r'\b(broken|not\s*working|stopped\s*working|damaged|faulty|malfunctioning|defective)\b',
    r'\b(making\s*(a\s*)?(loud\s*)?noise|sparking|short\s*circuit|leaking|leakage|overflowing)\b',
    r'\b(no\s*water|no\s*electricity|power\s*cut|power\s*outage|blackout|dirty|unclean|smell|stink|spoiled|theft|stolen|lost\s*item)\b',
    r'\b(ragging|harassment|threat|fight|abusive)\b',
    r'\b(i\s*want\s*to\s*report|help\s*me\s*report|lodge\s*a\s*complaint|file\s*a\s*complaint)\b',
    r'(खराब\s*है|टूट\s*गया|काम\s*नहीं\s*कर\s*रहा|पानी\s*नहीं\s*आ\s*रहा|बिजली\s*गुल|गंदगी|बदबू|शिकायत\s*दर्ज\s*करनी\s*है|रिपोर्ट\s*करना\s*है)',
    r'\b(paani\s*nahi\s*aarha|bijli\s*chali\s*gayi|fan\s*kharab\s*hai|light\s*nahi\s*chal\s*rahi)\b'
]

# Personal Complaint Tracking
PERSONAL_COMPLAINT_TRACKING_PATTERNS = [
    r'\b(how\s*(can\s*i|do\s*i|to)\s*(check|track|view)\s*(my\s*)?(active\s*)?complaints?)\b',
    r'\b(my\s*active\s*complaints?|status\s*of\s*my\s*complaints?|track\s*my\s*ticket)\b',
    r'\b(what\s*are\s*my\s*(active\s*)?complaints?|show\s*my\s*complaints?)\b',
    r'(मेरी\s*सक्रिय\s*शिकायतें|मेरी\s*शिकायतें\s*दिखाओ|मेरी\s*शिकायत\s*का\s*स्टेटस)',
    r'\b(meri\s*shikayat|shikayat\s*status|ticket\s*status)\b'
]


class IntentClassifier:
    """
    Evaluates student input and determines the precise intent.
    Enforces the Absolute Priority Rule: General questions must NEVER trigger complaints.
    """

    @classmethod
    def classify(cls, query: str, lang: str = 'en-IN') -> AssistantIntent:
        if not query or not query.strip():
            return AssistantIntent.GENERAL_KNOWLEDGE

        text = query.strip()
        text_lower = text.lower()

        # Step 1: Check if this is an explicit campus grievance reporting query
        has_defect_or_reporting = any(
            re.search(p, text_lower, re.IGNORECASE) or re.search(p, text, re.IGNORECASE)
            for p in CAMPUS_DEFECT_INDICATORS
        )

        is_educational_inquiry = re.search(
            r'^(what\s+is|what\s+are|define|explain|how\s+does|how\s+do|difference\s+between|write\s+a\s+program|write\s+code)\b',
            text_lower
        ) or re.search(r'(क्या\s*है|किसे\s*कहते|समझाओ|समझाइए|परिभाषा|अंतर\s*क्या)', text)

        if has_defect_or_reporting and not is_educational_inquiry:
            return AssistantIntent.CAMPUS_COMPLAINT

        # Step 2: Check for Edit or Delete Complaint Procedural Guidance
        if re.search(r'\b(edit|delete|modify|remove|withdraw|cancel)\s*(my\s*)?(complaint|application|ticket|grievance)\b', text_lower) or \
           re.search(r'(शिकायत\s*एडिट|शिकायत\s*डिलीट|आवेदन\s*में\s*संशोधन|शिकायत\s*हटाएं)', text):
            return AssistantIntent.WEBSITE_SUPPORT

        # Step 3: Check for Profile Photo & Profile Details Editing
        if re.search(r'\b(profile\s*(image|photo|picture)|edit\s*(my\s*)?image|change\s*(my\s*)?(photo|image|picture)|upload\s*(photo|image))\b', text_lower) or \
           re.search(r'\b(change|update|edit)\s*(my\s*)?(name|student\s*id|profile|address|details)\b', text_lower) or \
           re.search(r'(प्रोफाइल|फोटो\s*अपलोड|पासवर्ड\s*बदलें)', text):
            return AssistantIntent.WEBSITE_SUPPORT

        # Step 3b: Check for Voice Recording & Speech-to-Text Guidance
        if re.search(r'\b(voice\s*(reporting|recording|input|complaint)|speech\s*to\s*text|stt)\b', text_lower) or \
           re.search(r'(बोलकर\s*शिकायत|वॉइस\s*रिकॉर्डिंग|आवाज़\s*से\s*शिकायत)', text):
            return AssistantIntent.WEBSITE_SUPPORT

        # Step 4: Check for Website Navigation and Operational Procedures
        website_keywords = [
            'proofvoice', 'login', 'log in', 'sign in', 'logout', 'log out', 'sign out',
            'register', 'registration', 'student id', 'roll number', 'department',
            'institution', 'college list', 'unlisted', 'track complaint', 'status meaning',
            'under review', 'in progress', 'resolved', 'escalated', 'notification',
            'clear alerts', 'read aloud', 'tts', 'timbre', 'prisma'
        ]
        if any(re.search(r'\b' + re.escape(w) + r'\b', text_lower) for w in website_keywords) or \
           re.search(r'(लॉगिन|साइन\s*आउट|पंजीकरण|रजिस्ट्रेशन|संस्थान|स्टेटस|सूचनाएं|अलर्ट)', text):
            return AssistantIntent.WEBSITE_SUPPORT

        # Step 5: Default to GENERAL_KNOWLEDGE
        return AssistantIntent.GENERAL_KNOWLEDGE
