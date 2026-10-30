"""
AI Assistant Service for ProofVoice.
Provides NLP and AI services for:
- Summarization of student grievances
- Smart categorization and departmental routing
- Professional title generation
- Grammar & formal tone refinement preserving authentic student meaning
"""

import re
import logging

logger = logging.getLogger(__name__)

DEPARTMENT_CATEGORY_RULES = [
    {
        'category': 'HOSTEL',
        'department': 'Hostel Administration',
        'keywords': [
            'hostel', 'mess', 'food', 'canteen', 'room', 'bed', 'warden',
            'water cooler', 'geyser', 'dormitory', 'laundry', 'curfew', 'roommate',
            'hot water', 'drinking water', 'hostel fee'
        ],
        'default_priority': 'MEDIUM'
    },
    {
        'category': 'INFRASTRUCTURE',
        'department': 'Estate & Maintenance',
        'keywords': [
            'projector', 'fan', 'ac', 'air conditioner', 'light', 'tube light',
            'bench', 'desk', 'blackboard', 'whiteboard', 'door', 'window', 'lift',
            'elevator', 'water purifier', 'leakage', 'seepage', 'power cut',
            'switchboard', 'socket', 'wire', 'broken chair', 'generator'
        ],
        'default_priority': 'HIGH'
    },
    {
        'category': 'SANITARY',
        'department': 'Sanitation & Hygiene Services',
        'keywords': [
            'washroom', 'toilet', 'bathroom', 'sanitary', 'cleaning', 'garbage',
            'dustbin', 'smell', 'stench', 'flush', 'tap', 'drainage', 'choke',
            'hygiene', 'sweeper', 'pest', 'mosquito', 'insect'
        ],
        'default_priority': 'HIGH'
    },
    {
        'category': 'IT_SERVICES',
        'department': 'Information Technology Support',
        'keywords': [
            'wifi', 'wi-fi', 'internet', 'portal', 'erp', 'login', 'password',
            'lan', 'ethernet', 'server', 'network', 'router', 'system crash',
            'lab pc', 'computer', 'software', 'antivirus', 'connectivity'
        ],
        'default_priority': 'MEDIUM'
    },
    {
        'category': 'ACADEMIC',
        'department': 'Academic Affairs',
        'keywords': [
            'class', 'lecture', 'professor', 'faculty', 'teacher', 'attendance',
            'syllabus', 'internal', 'marks', 'exam', 'examination', 'hall ticket',
            'curriculum', 'grade', 'evaluation', 'assignment', 'lab session'
        ],
        'default_priority': 'HIGH'
    },
    {
        'category': 'LIBRARY',
        'department': 'Central Library',
        'keywords': [
            'library', 'book', 'books', 'librarian', 'reading room', 'journal',
            'digital library', 'fine', 'card', 'borrow', 'return', 'textbook'
        ],
        'default_priority': 'LOW'
    },
    {
        'category': 'SECURITY',
        'department': 'Campus Security & Discipline',
        'keywords': [
            'security', 'guard', 'theft', 'stolen', 'lost', 'harassment', 'ragging',
            'bullying', 'safety', 'cctv', 'parking', 'gate', 'unauthorized', 'threat'
        ],
        'default_priority': 'URGENT'
    },
    {
        'category': 'ADMINISTRATIVE',
        'department': 'Student Affairs & Registrar Office',
        'keywords': [
            'fee', 'receipt', 'scholarship', 'bonafide', 'certificate', 'bus pass',
            'transport', 'id card', 'refund', 'admission', 'document', 'verification'
        ],
        'default_priority': 'MEDIUM'
    }
]

URGENT_KEYWORDS = [
    'fire', 'electric shock', 'sparking', 'short circuit', 'ragging',
    'harassment', 'physical fight', 'injury', 'medical emergency', 'threat',
    'severe leak', 'flooding', 'poisonous', 'food poisoning', 'urgent', 'immediately'
]


class AiAssistantService:
    """
    Intelligent engine for analyzing, structuring, and improving complaint applications.
    Deterministic, robust fallback engine ensures 100% uptime with sub-second response times.
    """

    @classmethod
    def categorize_and_route(cls, text):
        """
        Analyzes grievance text to suggest category, responsible department, and priority.
        """
        if not text:
            return {
                'category': 'OTHER',
                'department': 'Student Affairs & Grievance Cell',
                'priority': 'MEDIUM',
                'confidence': 0.5
            }

        text_lower = text.lower()

        # Check for urgency triggers
        is_urgent = any(kw in text_lower for kw in URGENT_KEYWORDS)

        best_match = None
        max_score = 0

        for rule in DEPARTMENT_CATEGORY_RULES:
            score = 0
            for kw in rule['keywords']:
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    score += 2
                elif kw in text_lower:
                    score += 1

            if score > max_score:
                max_score = score
                best_match = rule

        if best_match and max_score > 0:
            suggested_priority = 'URGENT' if is_urgent else best_match['default_priority']
            confidence = min(0.95, round(0.5 + (max_score * 0.08), 2))
            return {
                'category': best_match['category'],
                'department': best_match['department'],
                'priority': suggested_priority,
                'confidence': confidence
            }

        return {
            'category': 'OTHER',
            'department': 'Student Affairs & Grievance Cell',
            'priority': 'URGENT' if is_urgent else 'MEDIUM',
            'confidence': 0.45
        }

    @classmethod
    def generate_title(cls, text, category=None):
        """
        Synthesizes a concise, professional title from a raw student grievance.
        """
        if not text:
            return "Campus Grievance Application"

        clean_text = text.strip()
        sentences = [s.strip() for s in re.split(r'[.\n!?]+', clean_text) if len(s.strip()) > 5]
        primary = sentences[0] if sentences else clean_text[:80]

        # Clean leading introductory preambles
        lead_fillers = [
            r'^(?:i\s+(?:want|wish)\s+to\s+report\s+that|i\s+am\s+writing\s+to\s+complain\s+about)\s*',
            r'^(?:respected\s+sir(?:/madam)?|sir|madam)\s*,?\s*',
            r'^(?:there\s+is\s+(?:an?\s+)?(?:problem|issue)\s+with)\s*',
            r'^(?:regarding(?:\s+the)?|with\s+regards\s+to)\s*'
        ]
        title_cand = primary
        for pattern in lead_fillers:
            title_cand = re.sub(pattern, '', title_cand, flags=re.IGNORECASE).strip()

        # Extract core hardware or facility subject
        match = re.search(
            r'\b(?:broken|malfunctioning|damaged|faulty|repair\s+of|issue\s+with|problem\s+with)\s+([A-Za-z0-9\s]+?)(?=\s+\b(?:in|at|on|due\s+to|since|from)\b|[.!?]|$)',
            title_cand,
            re.IGNORECASE
        )
        if match:
            item = match.group(1).strip()
            if len(item) >= 3:
                return f"Urgent Grievance: Malfunctioning {item.title()}"

        words = title_cand.split()
        if len(words) > 10:
            title_cand = " ".join(words[:9])

        title_cand = title_cand.rstrip('.,;:')
        if not title_cand:
            return f"Grievance Regarding Campus {category.replace('_', ' ').title() if category else 'Facilities'}"

        return title_cand[:90].strip().title()

    @classmethod
    def summarize(cls, text, max_sentences=2):
        """
        Distills the primary grievance and impact into an executive summary.
        """
        if not text:
            return "No grievance description provided."

        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', text) if len(s.strip()) > 8]
        if not sentences:
            return text[:150]

        if len(sentences) <= max_sentences:
            return " ".join(sentences)

        # Retain opening thesis sentence and conclusion/impact sentence
        key_sentences = [sentences[0]]
        for s in sentences[1:]:
            s_low = s.lower()
            if any(k in s_low for k in ['causing', 'disruption', 'unable', 'affect', 'request', 'immediate', 'urgent', 'repair']):
                key_sentences.append(s)
                break

        if len(key_sentences) < max_sentences and len(sentences) > 1:
            key_sentences.append(sentences[1])

        return " ".join(key_sentences)

    @classmethod
    def refine_grammar(cls, text):
        """
        Polishes spelling, structure, and formal tone while strictly preserving
        the student's factual statements, context, and meaning.
        """
        if not text:
            return ""

        refined = text.strip()

        # Fix common informal contractions and colloquial academic expressions
        substitutions = [
            (r'\bplz\b|\bpls\b', 'please'),
            (r'\bu\b', 'you'),
            (r'\bur\b', 'your'),
            (r'\br\b', 'are'),
            (r'\bgovt\b', 'government'),
            (r'\bwont\b', "won't"),
            (r'\bcant\b', "cannot"),
            (r'\bdont\b', "do not"),
            (r'\bdidnt\b', "did not"),
            (r'\bisnt\b', "is not"),
            (r'\bwasnt\b', "was not"),
            (r'\bhavent\b', "have not"),
            (r'\bhasnt\b', "has not"),
            (r'\basap\b', 'at the earliest possible convenience'),
            (r'\badmin\b', 'administration'),
            (r'\bproff?\b', 'professor'),
            (r'\bwifi\b', 'Wi-Fi'),
            (r'\bac\b', 'Air Conditioner (AC)'),
            (r'\bhostel\s+warden\b', 'Hostel Warden')
        ]

        for pattern, repl in substitutions:
            refined = re.sub(pattern, repl, refined, flags=re.IGNORECASE)

        # Normalize sentence capitalization
        refined_sentences = []
        for raw_s in re.split(r'([.!?]+(?:\s+|\n+|$))', refined):
            if not raw_s:
                continue
            if re.match(r'^[.!?]+(?:\s+|\n+|$)', raw_s):
                refined_sentences.append(raw_s)
            else:
                s_stripped = raw_s.strip()
                if s_stripped:
                    capitalized = s_stripped[0].upper() + s_stripped[1:]
                    refined_sentences.append(capitalized)

        refined = "".join(refined_sentences)

        # Ensure terminal punctuation
        if refined and not refined.endswith(('.', '!', '?')):
            refined += '.'

        return refined

    @classmethod
    def process_complete_grievance(cls, text, user=None, institution=None):
        """
        Comprehensive AI pipeline:
        Takes raw grievance transcript or text and delivers complete structured packet.
        """
        routing = cls.categorize_and_route(text)
        title = cls.generate_title(text, category=routing['category'])
        summary = cls.summarize(text)
        refined_description = cls.refine_grammar(text)

        return {
            'title': title,
            'category': routing['category'],
            'suggested_department': routing['department'],
            'suggested_priority': routing['priority'],
            'confidence': routing['confidence'],
            'summary': summary,
            'refined_description': refined_description,
            'original_description': text
        }
