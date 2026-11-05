# -*- coding: utf-8 -*-
"""
ProofVoice Comprehensive Platform Knowledge Base.
Provides verified, exact, step-by-step guidance in English and Hindi for:
- Sign Out & Authentication Lifecycle
- Student Registration & Institution Affiliation
- Institution Registration & Staff Access Requests
- Login & Password Troubleshooting
- Student Dashboard & Tracking Metrics
- Institution Admin Grievance Management & Resolution
- Platform Super Admin Command Hub & Campus Verification
- Voice & Text Grievance Filing (Gnani AI Prisma STT)
- Editing & Withdrawing Submitted Applications
- Complaint Statuses & SLA Milestones
- Personalized Notifications Center
- Profile Credentials, Photo Upload & Password Updates
- Speech Accessibility & Text-to-Speech (Gnani Timbre TTS)
- Privacy, Tenant Isolation & Role Permissions
"""
import re

CAMPUS_KNOWLEDGE_TOPICS = {
    'sign_out': {
        'patterns': [
            r'\b(sign\s*out|log\s*out|logout|signout|exit\s*account|close\s*session)\b',
            r'\b(sign\s*out\s*(kaise|karein|karna)|logout\s*kaise)\b',
            r'(लॉग\s*आउट|साइन\s*आउट|लॉगआउट|साइनआउट|बाहर\s*कैसे\s*निकलें)'
        ],
        'replies': {
            'en-IN': (
                "**How to Sign Out of ProofVoice:**\n\n"
                "1. Locate the **left sidebar navigation** on your dashboard.\n"
                "2. Near the bottom (just above your profile avatar card), you will find the red **'Sign Out'** button (`[-> Sign Out`).\n"
                "3. Click **'Sign Out'** to safely terminate your active session.\n"
                "4. Your authentication tokens and local credentials will be cleared, redirecting you securely to the **Main Login Page** (`login.html`).\n\n"
                "💡 *Security Tip:* Always sign out when accessing ProofVoice from shared campus computer labs or public terminals."
            ),
            'hi-IN': (
                "**ProofVoice से साइन आउट (Logout) करने के चरण:**\n\n"
                "1. अपने डैशबोर्ड के **बाएं साइडबार मेनू** को देखें।\n"
                "2. सबसे नीचे, अपने प्रोफाइल कार्ड के ठीक ऊपर आपको लाल रंग का **'Sign Out'** बटन (`[-> Sign Out`) दिखाई देगा।\n"
                "3. **'Sign Out'** पर क्लिक करें।\n"
                "4. आपका सत्र सुरक्षित रूप से समाप्त हो जाएगा और आप मुख्य **लॉगिन पेज** (`login.html`) पर वापस पहुंच जाएंगे।\n\n"
                "💡 *सुरक्षा सुझाव:* लाइब्रेरी या सार्वजनिक कंप्यूटर पर काम पूरा होने के बाद हमेशा साइन आउट करें।"
            )
        },
        'suggested_actions': {
            'en-IN': ["Sign Out Now", "View My Complaints", "Profile & Settings"],
            'hi-IN': ["अभी साइन आउट करें", "मेरी शिकायतें", "प्रोफाइल और सेटिंग्स"]
        }
    },

    'student_registration': {
        'patterns': [
            r'\b(student\s*registration|register\s*as\s*student|new\s*student\s*account|create\s*student\s*account)\b',
            r'\b(unlisted\s*institution|college\s*not\s*listed|not\s*in\s*list)\b',
            r'\b(student\s*register\s*kaise|nayi\s*id\s*kaise\s*banaye)\b',
            r'(छात्र\s*पंजीकरण|रजिस्ट्रेशन\s*कैसे\s*करें|नया\s*खाता\s*बनाएं|कॉलेज\s*सूची\s*में\s*नहीं)'
        ],
        'replies': {
            'en-IN': (
                "**How to Register as a Student on ProofVoice:**\n\n"
                "1. Open the **Student Registration** page (`register.html`).\n"
                "2. **Select Institution:** Choose your verified college from the dropdown list. If your college is not listed, click **'+ My Institution Is Not Listed'** and provide the name, city, state, and official domain.\n"
                "3. **Academic Details:** Enter your **Full Legal Name**, **Institutional Email**, and choose a secure password (min 8 characters).\n"
                "4. Select your **Academic Department / Course**, **Year / Semester**, and enter your **Student ID / Roll Number**.\n"
                "5. Provide your **Residential Address** (hostel room or home address, which auto-populates formal letters).\n"
                "6. Click **'Create Verified Student Account'** to gain instant access to your student dashboard."
            ),
            'hi-IN': (
                "**ProofVoice में छात्र पंजीकरण (Student Registration) के चरण:**\n\n"
                "1. **Student Registration** पेज (`register.html`) पर जाएं।\n"
                "2. **संस्थान चुनें:** ड्रॉपडाउन से अपना कॉलेज चुनें। यदि आपका कॉलेज सूची में नहीं है, तो **'+ My Institution Is Not Listed'** चुनें और विवरण दर्ज करें।\n"
                "3. अपना **पूरा नाम**, **ईमेल आईडी**, और कम से कम 8 अक्षरों का सुरक्षित पासवर्ड भरें।\n"
                "4. अपना **विभाग (Department)**, **सेमेस्टर**, और **छात्र आईडी (Roll No)** दर्ज करें।\n"
                "5. अपना आवासीय पता भरें (यह औपचारिक शिकायत पत्रों में स्वतः जुड़ जाता है)।\n"
                "6. **'Create Verified Student Account'** पर क्लिक करें। आपका खाता तुरंत सक्रिय हो जाएगा।"
            )
        },
        'suggested_actions': {
            'en-IN': ["Open Registration Page", "Student Login", "Help & Support"],
            'hi-IN': ["रजिस्ट्रेशन पेज खोलें", "छात्र लॉगिन", "सहायता और सपोर्ट"]
        }
    },

    'institution_onboarding': {
        'patterns': [
            r'\b(register\s*(a\s*)?new\s*institution|institution\s*registration|request\s*access\s*to\s*existing|admin\s*access\s*request)\b',
            r'\b(college\s*register|institution\s*onboarding|super\s*admin\s*approval)\b',
            r'\b(institute\s*kaise\s*jode|admin\s*access\s*kaise)\b',
            r'(संस्थान\s*पंजीकरण|नया\s*कॉलेज\s*जोड़ें|एडमिन\s*एक्सेस\s*अनुरोध|सुपर\s*एडमिन\s*मंजूरी)'
        ],
        'replies': {
            'en-IN': (
                "**Institution Registration & Administrator Access:**\n\n"
                "ProofVoice provides two distinct onboarding pathways at `institution-register.html`:\n\n"
                "• **Path 1: Request Access to Existing Institution:** Staff members or faculty seeking grievance redressal privileges for a registered campus can submit their official credentials, department, and designation. This request is sent to the campus administration and Super Admin for vetting.\n"
                "• **Path 2: Register New Institution:** Campus leadership (Dean, Principal, Registrar) can register a new institutional workspace by submitting institution type, official email, address, official domain, and accreditation documents.\n\n"
                "🔍 **Approval Rule:** For security, duplicate requests for the same institution name or email are rejected. Super Admins review documentation in the Super Admin Console before approving activation."
            ),
            'hi-IN': (
                "**संस्थान पंजीकरण एवं व्यवस्थापक एक्सेस:**\n\n"
                "ProofVoice में `institution-register.html` पर दो विकल्प उपलब्ध हैं:\n\n"
                "• **विकल्प 1: मौजूदा संस्थान के लिए एक्सेस अनुरोध:** यदि आपका कॉलेज पहले से रजिस्टर्ड है, तो शिक्षक या अधिकारी अपनी आधिकारिक ईमेल और पद भरकर एडमिन एक्सेस का अनुरोध कर सकते हैं।\n"
                "• **विकल्प 2: नया संस्थान पंजीकृत करें:** कॉलेज प्रबंधन (डीन/प्राचार्य) अपने कॉलेज का नाम, आधिकारिक ईमेल, पता और सत्यापन दस्तावेज जमा करके नए डिजिटल कार्यक्षेत्र का पंजीकरण कर सकते हैं।\n\n"
                "🔍 **सत्यापन नियम:** एक संस्थान या ईमेल के लिए केवल एक ही सक्रिय अनुरोध स्वीकार होता है। प्लेटफॉर्म सुपर एडमिन द्वारा समीक्षा के बाद ही इसे सक्रिय किया जाता है।"
            )
        },
        'suggested_actions': {
            'en-IN': ["Institution Register Page", "Super Admin Console", "Help & Support"],
            'hi-IN': ["संस्थान रजिस्ट्रेशन पेज", "सुपर एडमिन कंसोल", "सहायता"]
        }
    },

    'login_troubleshooting': {
        'patterns': [
            r'\b(login\s*problem|cannot\s*login|can\'?t\s*login|wrong\s*password|login\s*failed|unable\s*to\s*sign\s*in|forgot\s*password)\b',
            r'\b(login\s*nahi\s*ho\s*raha|password\s*bhul\s*gaya|password\s*galat)\b',
            r'(लॉगिन\s*नहीं\s*हो\s*रहा|पासवर्ड\s*गलत|पासवर्ड\s*भूल\s*गया|लॉगिन\s*समस्या)'
        ],
        'replies': {
            'en-IN': (
                "**Troubleshooting ProofVoice Login:**\n\n"
                "1. **Email Address:** Enter the exact institutional email used during registration. Emails are checked case-insensitively.\n"
                "2. **Password Security:** Passwords are case-sensitive and hashed using PBKDF2 with SHA-256. If you recently updated your password in *Profile & Settings*, use your newest password.\n"
                "3. **Forgot Password:** Click **'Forgot Password?'** (`forgot-password.html`) on the login screen to receive a secure password reset link.\n"
                "4. **Demo Testing Credentials:**\n"
                "   • Verified Student: `laxmi.seth@apex.edu` (Password: `Student@123`)\n"
                "   • Institution Admin: `rajkr@apex.edu` (Password: `Admin@123`)\n"
                "   • Super Admin: `superadmin@proofvoice.platform`"
            ),
            'hi-IN': (
                "**लॉगिन समस्याओं का समाधान:**\n\n"
                "1. **ईमेल की जांच करें:** वही ईमेल दर्ज करें जो आपने रजिस्ट्रेशन में दिया था।\n"
                "2. **पासवर्ड की शुद्धता:** पासवर्ड केस-सेंसिटिव होता है। यदि आपने हाल ही में प्रोफाइल में पासवर्ड बदला है, तो नया पासवर्ड ही दर्ज करें।\n"
                "3. **पासवर्ड भूल गए:** लॉगिन स्क्रीन पर **'Forgot Password?'** (`forgot-password.html`) पर क्लिक करके पासवर्ड रीसेट लिंक प्राप्त करें।\n"
                "4. **परीक्षण के लिए डेमो खाते:**\n"
                "   • छात्र: `laxmi.seth@apex.edu` (पासवर्ड: `Student@123`)\n"
                "   • कॉलेज एडमिन: `rajkr@apex.edu` (पासवर्ड: `Admin@123`)\n"
                "   • सुपर एडमिन: `superadmin@proofvoice.platform`"
            )
        },
        'suggested_actions': {
            'en-IN': ["Go to Login Page", "Forgot Password", "Register New Account"],
            'hi-IN': ["लॉगिन पेज पर जाएं", "पासवर्ड रीसेट करें", "नया खाता बनाएं"]
        }
    },

    'student_dashboard': {
        'patterns': [
            r'\b(student\s*dashboard|student\s*overview|how\s*to\s*use\s*student\s*dashboard|dashboard\s*features)\b',
            r'\b(student\s*dashboard\s*kaise|dashboard\s*me\s*kya\s*hai)\b',
            r'(छात्र\s*डैशबोर्ड|स्टूडेंट\s*डैशबोर्ड|डैशबोर्ड\s*सुविधाएं)'
        ],
        'replies': {
            'en-IN': (
                "**ProofVoice Student Dashboard (`student-dashboard.html`):**\n\n"
                "• **Overview Metrics:** View real-time metric cards for Total Complaints, In Progress, Under Review, and Resolved.\n"
                "• **Quick Filing:** Click the **'+ New Complaint'** button in the header or sidebar to report issues via voice or text.\n"
                "• **Active Grievances Roster:** View recent ticket progress with live color-coded status badges and assigned department tags.\n"
                "• **AI Campus Assistant:** Access the built-in bilingual AI Assistant anytime via the Help & Support tab (`student-help.html`).\n"
                "• **Notifications:** Real-time bell alert counter showing administrative remarks and status changes."
            ),
            'hi-IN': (
                "**ProofVoice छात्र डैशबोर्ड (`student-dashboard.html`):**\n\n"
                "• **मुख्य मैट्रिक्स:** कुल शिकायतें, समीक्षाधीन (Under Review), प्रगति पर (In Progress), और सुलझाई गई (Resolved) शिकायतों की लाइव स्थिति।\n"
                "• **त्वरित शिकायत:** शीर्ष पर **'+ New Complaint'** बटन दबाकर बोलकर या लिखकर शिकायत दर्ज करें।\n"
                "• **सक्रिय शिकायतों की सूची:** प्रत्येक शिकायत की स्थिति, विभाग और तारीख तुरंत देखें।\n"
                "• **AI कैंपस सहायक:** `student-help.html` पर हिंदी और अंग्रेजी में AI सहायक से मदद लें।\n"
                "• **नोटिफिकेशन:** अधिकारियों की टिप्पणी और स्थिति में बदलाव पर लाइव अलर्ट प्राप्त करें।"
            )
        },
        'suggested_actions': {
            'en-IN': ["Open Student Dashboard", "Create Complaint", "My Complaints"],
            'hi-IN': ["छात्र डैशबोर्ड खोलें", "शिकायत दर्ज करें", "मेरी शिकायतें"]
        }
    },

    'admin_dashboard': {
        'patterns': [
            r'\b(admin\s*dashboard|institution\s*panel|manage\s*complaints\s*desk|assign\s*department|assign\s*technician)\b',
            r'\b(admin\s*panel|campus\s*users|admin\s*remarks|internal\s*notes)\b',
            r'\b(admin\s*kaise\s*chalaye|complaint\s*assign\s*kaise)\b',
            r'(व्यवस्थापक\s*डैशबोर्ड|संस्थान\s*पैनल|शिकायत\s*प्रबंधन|विभाग\s*आवंटन|एडमिन\s*टिप्पणी)'
        ],
        'replies': {
            'en-IN': (
                "**ProofVoice Institution Administrator Panel (`admin-dashboard.html`):**\n\n"
                "• **Grievance Triage:** Review incoming grievances submitted by students across your campus.\n"
                "• **Review & Action Desk (`admin-complaint-details.html`):**\n"
                "  - Change status (Under Review, In Progress, Resolved).\n"
                "  - Route complaint to relevant departments (Estate, IT, Hostel, Academic).\n"
                "  - Assign technicians or faculty officers by name.\n"
                "  - Post **Public Remarks** visible on the student's progress timeline.\n"
                "  - Record **Confidential Internal Notes** visible only to authorized administrators.\n"
                "• **Campus Users Desk (`users.html`):** Inspect registered students, verify student IDs, and approve or reject staff access requests."
            ),
            'hi-IN': (
                "**संस्थान व्यवस्थापक (Admin) पैनल (`admin-dashboard.html`):**\n\n"
                "• **शिकायत प्रबंधन:** परिसर के छात्रों द्वारा दर्ज की गई सभी शिकायतों की समीक्षा करें।\n"
                "• **कार्यवाही डेस्क (`admin-complaint-details.html`):**\n"
                "  - स्थिति बदलें (Under Review, In Progress, Resolved)।\n"
                "  - संबंधित विभाग (आईटी, मेंटेनेंस, हॉस्टल) को शिकायत आवंटित करें।\n"
                "  - फील्ड तकनीशियन या अधिकारी का नाम नियुक्त करें।\n"
                "  - छात्र की टाइमलाइन पर **सार्वजनिक टिप्पणी (Public Remark)** दर्ज करें।\n"
                "  - केवल एडमिन के लिए **गोपनीय आंतरिक नोट (Internal Note)** लिखें।\n"
                "• **कैंपस उपयोगकर्ता डेस्क (`users.html`):** छात्रों के रोल नंबर सत्यापित करें और नए स्टाफ एक्सेस आवेदनों को स्वीकार या अस्वीकार करें।"
            )
        },
        'suggested_actions': {
            'en-IN': ["Admin Complaints Desk", "Campus Users Management", "Help & Support"],
            'hi-IN': ["एडमिन शिकायत डेस्क", "उपयोगकर्ता प्रबंधन", "सहायता"]
        }
    },

    'super_admin_dashboard': {
        'patterns': [
            r'\b(super\s*admin|platform\s*super\s*admin|super\s*admin\s*dashboard|super\s*admin\s*console)\b',
            r'\b(approve\s*institution|reject\s*institution|active\s*institutions|multi\s*tenant\s*gateway)\b',
            r'\b(super\s*admin\s*kya\s*karta|console\s*kaise)\b',
            r'(सुपर\s*एडमिन|प्लेटफॉर्म\s*कंसोल|संस्थान\s*स्वीकृति|ग्लोबल\s*प्रबंधन)'
        ],
        'replies': {
            'en-IN': (
                "**Platform Super Admin Console (`super-admin/dashboard/`):**\n\n"
                "• **Centralized Oversight:** Oversees multi-tenant operations across all universities and colleges.\n"
                "• **Institutional Requests (`#pending-inst`):** Review official campus registration requests, inspect submitted accreditation documents, and approve or reject institutional workspaces.\n"
                "• **Staff & Admin Access Requests (`#admin-access-requests`):** Review requests from faculty and staff requesting administrative access to existing campuses.\n"
                "• **Active Institutions:** Monitor verified institutions, view student headcounts, and suspend or unsuspend non-compliant campuses.\n"
                "• **Strict Deduplication:** Displays exactly one row per institution and email with accurate pending badges."
            ),
            'hi-IN': (
                "**प्लेटफॉर्म सुपर एडमिन कंसोल (`super-admin/dashboard/`):**\n\n"
                "• **केंद्रीकृत नियंत्रण:** सभी संबद्ध विश्वविद्यालयों और कॉलेजों के कार्यों की निगरानी करता है।\n"
                "• **संस्थान पंजीकरण अनुरोध (`#pending-inst`):** नए कॉलेज आवेदनों और दस्तावेजों की जांच करके उन्हें स्वीकृत या अस्वीकृत करता है।\n"
                "• **स्टाफ एक्सेस अनुरोध (`#admin-access-requests`):** मौजूदा संस्थानों में एडमिन बनने के आवेदनों की समीक्षा करता है।\n"
                "• **सक्रिय संस्थान सूची:** सभी सक्रिय कॉलेजों की छात्र संख्या और स्थिति की निगरानी।\n"
                "• **डुप्लीकेट सुरक्षा:** एक संस्थान और ईमेल का केवल एक ही आवेदन सूची में दिखता है।"
            )
        },
        'suggested_actions': {
            'en-IN': ["Open Super Admin Console", "Institutional Requests", "Active Campuses"],
            'hi-IN': ["सुपर एडमिन कंसोल खोलें", "संस्थान अनुरोध", "सक्रिय कॉलेज"]
        }
    },

    'create_complaint': {
        'patterns': [
            r'\b((create|file|lodge|submit|post|make|register)\s*(a\s*)?(new\s*)?(complaint|grievance|issue|ticket))\b',
            r'\b(how\s*(do\s*i|can\s*i|to)\s*(create|file|lodge|submit|make|register)\s*(a\s*)?(complaint|grievance|issue))\b',
            r'\b(voice\s*reporting|record\s*complaint|microphone\s*input|speak\s*complaint)\b',
            r'\b(shikayat\s*(kaise|karein|darj)|bolkar\s*shikayat)\b',
            r'(शिकायत\s*कैसे\s*दर्ज\s*करें|समस्या\s*की\s*रिपोर्ट|बोलकर\s*शिकायत|नई\s*शिकायत|आवाज\s*से\s*शिकायत)'
        ],
        'replies': {
            'en-IN': (
                "**How to File a Campus Grievance (Voice or Text):**\n\n"
                "1. Click **'+ New Complaint'** (`new-complaint.html`) from your dashboard or sidebar.\n"
                "2. **Category & Department:** Choose the relevant facility (e.g. Classroom & Lab, Hostel, Electrical, Sanitation, IT Support).\n"
                "3. **Location Details:** Provide the exact building, block, or room number.\n"
                "4. **Voice or Text Input:**\n"
                "   • **Voice:** Tap the 🎙️ **Microphone** button to speak naturally in **English or Hindi**. Gnani AI Prisma STT transcribes your speech live. Review and edit the transcription before generating your letter.\n"
                "   • **Text:** Or type the details directly in the problem description box.\n"
                "5. **Formal Application Review:** ProofVoice automatically formats a formal institutional grievance letter addressed to the Principal or Dean.\n"
                "6. **Mandatory Declaration:** Check the confirmation box and click **'Submit Authoritative Complaint'** to receive your tracking ID (`PV-2026-XXXX`)."
            ),
            'hi-IN': (
                "**शिकायत दर्ज करने के चरण (बोलकर या लिखकर):**\n\n"
                "1. डैशबोर्ड से **'+ New Complaint'** (`new-complaint.html`) पर जाएं।\n"
                "2. **श्रेणी व विभाग:** संबंधित श्रेणी चुनें (जैसे क्लासरूम/लैब, हॉस्टल, बिजली, पानी, इंटरनेट)।\n"
                "3. **स्थान:** सटीक कमरा नंबर, लैब या हॉस्टल ब्लॉक दर्ज करें।\n"
                "4. **वॉइस या टेक्स्ट द्वारा विवरण:**\n"
                "   • **बोलकर:** 🎙️ **माइक बटन** दबाएं और **हिंदी या अंग्रेजी** में स्वाभाविक रूप से बोलें। Gnani AI Prisma इसे तुरंत टाइप कर देगा। आप सबमिट करने से पहले टेक्स्ट की समीक्षा व संशोधन कर सकते हैं।\n"
                "   • **लिखकर:** सीधे विवरण बॉक्स में टाइप करें।\n"
                "5. **औपचारिक पत्र:** सिस्टम स्वतः प्राचार्य/डीन के नाम एक औपचारिक पत्र तैयार करेगा।\n"
                "6. घोषणा बॉक्स पर टिक करके **'Submit Authoritative Complaint'** दबाएं और ट्रैकिंग आईडी (`PV-2026-XXXX`) प्राप्त करें।"
            )
        },
        'suggested_actions': {
            'en-IN': ["Create Complaint Now", "My Complaints", "Complaint Status Meanings"],
            'hi-IN': ["अभी शिकायत दर्ज करें", "मेरी शिकायतें", "शिकायत स्टेटस के अर्थ"]
        }
    },

    'edit_delete_complaint': {
        'patterns': [
            r'\b(edit\s*(my\s*)?complaint|delete\s*(my\s*)?complaint|withdraw\s*(my\s*)?complaint|edit\s*application|delete\s*application)\b',
            r'\b(shikayat\s*(badle|delete|hataye|sudhare|wapas))\b',
            r'(शिकायत\s*एडिट|शिकायत\s*डिलीट|आवेदन\s*में\s*संशोधन|शिकायत\s*हटाएं|शिकायत\s*वापस)'
        ],
        'replies': {
            'en-IN': (
                "**How to Edit or Withdraw a Submitted Complaint:**\n\n"
                "1. Navigate to **'My Complaints'** (`my-complaints.html`) from your sidebar menu.\n"
                "2. Click the **'View'** button on the ticket you wish to update to open `complaint-details.html`.\n"
                "3. **To Edit:** Click the **'Edit Application'** button. Modify your subject, room location, or description, and click *'Save Changes'*. Updates reflect on the institutional review desk immediately.\n"
                "4. **To Delete / Withdraw:** Click the red **'Delete Application'** button. Confirm the prompt to withdraw the grievance from administrative review."
            ),
            'hi-IN': (
                "**दर्ज शिकायत को संपादित (Edit) या वापस (Delete) लेने के चरण:**\n\n"
                "1. साइडबार मेनू से **'My Complaints'** (`my-complaints.html`) खोलें।\n"
                "2. जिस शिकायत को बदलना चाहते हैं, उसके सामने **'View'** बटन दबाएं।\n"
                "3. **संशोधन (Edit):** **'Edit Application'** बटन दबाएं, कमरा नंबर या विवरण अपडेट करें और *'Save Changes'* दबाएं।\n"
                "4. **हटाना (Delete):** लाल रंग का **'Delete Application'** बटन दबाएं और पुष्टि करें। शिकायत वापस ले ली जाएगी।"
            )
        },
        'suggested_actions': {
            'en-IN': ["View My Complaints", "Create New Complaint", "Help & Support"],
            'hi-IN': ["मेरी शिकायतें देखें", "नई शिकायत दर्ज करें", "सहायता"]
        }
    },

    'complaint_status': {
        'patterns': [
            r'\b(complaint\s*status|status\s*meanings|track\s*complaint|what\s*does\s*status\s*mean|status\s*lifecycle)\b',
            r'\b(under\s*review|in\s*progress|assigned|awaiting\s*student|resolved|reopened)\b',
            r'\b(shikayat\s*ka\s*status|status\s*ka\s*matlab)\b',
            r'(शिकायत\s*की\s*स्थिति|स्टेटस\s*का\s*मतलब|स्टेटस\s*का\s*अर्थ|ट्रैकिंग\s*स्थिति)'
        ],
        'replies': {
            'en-IN': (
                "**ProofVoice Grievance Lifecycle & Status Meanings:**\n\n"
                "• **Submitted:** Grievance recorded with an authoritative tracking ID and awaiting initial triage.\n"
                "• **Under Review:** The department head or administrative officer is actively reviewing your application.\n"
                "• **Assigned:** The ticket has been routed to a specific campus division and assigned technician.\n"
                "• **In Progress:** Technicians or contractors are on site executing repairs or maintenance.\n"
                "• **Awaiting Student:** The officer posted a public remark requesting clarification or photo evidence.\n"
                "• **Resolved:** Repairs completed and verified with closing remarks posted.\n"
                "• **Reopened:** If the problem recurs within warranty, you can reopen the resolved ticket directly."
            ),
            'hi-IN': (
                "**शिकायत जीवनचक्र और स्टेटस के अर्थ:**\n\n"
                "• **Submitted (दर्ज):** शिकायत को ट्रैकिंग आईडी मिल चुकी है और वह समीक्षा की प्रतीक्षा में है।\n"
                "• **Under Review (समीक्षाधीन):** संबंधित विभागाध्यक्ष द्वारा आवेदन का अध्ययन किया जा रहा है।\n"
                "• **Assigned (आवंटित):** समस्या के समाधान हेतु तकनीशियन या कर्मचारी नियुक्त कर दिया गया है।\n"
                "• **In Progress (प्रगति पर):** स्थल पर मरम्मत या निवारण कार्य चल रहा है।\n"
                "• **Awaiting Student (छात्र से जानकारी अपेक्षित):** आपसे अतिरिक्त फोटो या विवरण मांगा गया है।\n"
                "• **Resolved (सुलझाई गई):** कार्य पूर्ण कर दिया गया है और आधिकारिक टिप्पणी दर्ज है।\n"
                "• **Reopened (पुनः खोली गई):** यदि समस्या फिर से आती है, तो आप टिकट दोबारा खोल सकते हैं।"
            )
        },
        'suggested_actions': {
            'en-IN': ["Check My Complaints Status", "How to edit complaint?", "Help & Support"],
            'hi-IN': ["मेरी शिकायतों का स्टेटस", "शिकायत एडिट कैसे करें?", "सहायता"]
        }
    },

    'notifications': {
        'patterns': [
            r'\b(notifications?|alerts?|bell\s*icon|unread\s*notifications?|mark\s*as\s*read|delete\s*notification)\b',
            r'\b(notification\s*kaise|alert\s*kaise)\b',
            r'(सूचनाएं|नोटिफिकेशन|अलर्ट|घंटी\s*का\s*निशान|नोटिफिकेशन\s*हटाएं)'
        ],
        'replies': {
            'en-IN': (
                "**ProofVoice Notification System (`student-notifications.html`):**\n\n"
                "• **Event-Driven Alerts:** You only receive notifications when concrete actions occur (status updates, department assignments, admin remarks, or ticket resolution).\n"
                "• **Bell Counter:** The bell icon in the top header displays unread alert badges in real time.\n"
                "• **Manage Alerts:** In the Notifications Center, filter unread alerts, click any notification to jump directly to the complaint timeline, or click the red **Delete** button to clear alerts."
            ),
            'hi-IN': (
                "**ProofVoice नोटिफिकेशन सिस्टम (`student-notifications.html`):**\n\n"
                "• **सटीक अलर्ट:** आपको केवल महत्वपूर्ण घटनाओं (स्थिति में बदलाव, विभाग आवंटन, एडमिन की टिप्पणी या समाधान) पर ही सूचनाएं मिलती हैं।\n"
                "• **घंटी आइकन:** हेडर में घंटी का निशान नए संदेशों की संख्या तुरंत दिखाता है।\n"
                "• **अलर्ट प्रबंधन:** नोटिफिकेशन सेंटर में सीधे शिकायत पर जाएं या लाल **Delete** बटन दबाकर पुराने संदेश हटाएं।"
            )
        },
        'suggested_actions': {
            'en-IN': ["Open Notifications", "View My Complaints", "Profile & Settings"],
            'hi-IN': ["नोटिफिकेशन खोलें", "मेरी शिकायतें", "प्रोफाइल"]
        }
    },

    'profile_and_photo': {
        'patterns': [
            r'\b(profile|profile\s*photo|upload\s*photo|change\s*photo|change\s*password|update\s*profile|student\s*id|roll\s*number)\b',
            r'\b(photo\s*kaise\s*lagaye|password\s*kaise\s*badle|profile\s*update)\b',
            r'(प्रोफाइल\s*फोटो|फोटो\s*अपलोड|पासवर्ड\s*बदलें|प्रोफाइल\s*अपडेट|रोल\s*नंबर)'
        ],
        'replies': {
            'en-IN': (
                "**Profile, Photo Upload & Password Management (`student-profile.html`):**\n\n"
                "• **Academic Credentials:** Update your legal name, student ID / roll number, department, semester, and residential address.\n"
                "• **Profile Picture Upload:** Under Profile Picture, click **'Upload Photo'** (supports JPG, PNG, WebP up to 5MB). Crop preview live and click **'Save Photo'**.\n"
                "• **Change Password:** Scroll to the Password section, enter your current password, type your new password (minimum 8 characters), and click **'Update Password'**."
            ),
            'hi-IN': (
                "**प्रोफाइल, फोटो और पासवर्ड प्रबंधन (`student-profile.html`):**\n\n"
                "• **विवरण अपडेट:** अपना नाम, छात्र आईडी, विभाग, सेमेस्टर और आवासीय पता अपडेट करें।\n"
                "• **फोटो अपलोड:** **'Upload Photo'** पर क्लिक करें (JPG, PNG, WebP 5MB तक)। लाइव प्रीव्यू देखकर **'Save Photo'** दबाएं।\n"
                "• **पासवर्ड बदलना:** वर्तमान पासवर्ड और नया पासवर्ड (कम से कम 8 अक्षर) दर्ज करके **'Update Password'** पर क्लिक करें।"
            )
        },
        'suggested_actions': {
            'en-IN': ["Open Profile & Settings", "Change Password", "My Complaints"],
            'hi-IN': ["प्रोफाइल और सेटिंग्स खोलें", "पासवर्ड बदलें", "मेरी शिकायतें"]
        }
    },

    'voice_accessibility': {
        'patterns': [
            r'\b(voice\s*mode|text\s*to\s*speech|tts|read\s*aloud|listen\s*audio|gnani\s*timbre|ai\s*voice)\b',
            r'\b(bolkar\s*sunao|aawaz\s*me\s*sunao|voice\s*kaise)\b',
            r'(बोलकर\s*सुनाएं|आवाज\s*में\s*सुनें|टेक्स्ट\s*टू\s*स्पीच|वॉइस\s*मोड)'
        ],
        'replies': {
            'en-IN': (
                "**ProofVoice Speech Accessibility (Gnani AI Timbre TTS):**\n\n"
                "• **Read Aloud:** On complaint review and details screens, click the **'Read Aloud'** button to listen to formal letters or administrative responses.\n"
                "• **AI Assistant Voice Mode:** In this Help Assistant, toggle **'Voice Mode'** ON to receive spoken voice answers automatically.\n"
                "• **Playback Controls:** Use the interactive player bar to **Play**, **Pause**, or **Stop** audio anytime.\n"
                "• **Supported Languages:** Operates seamlessly in **English and Hindi**."
            ),
            'hi-IN': (
                "**वॉइस और टेक्स्ट-टू-स्पीच सुविधा (Gnani AI Timbre):**\n\n"
                "• **बोलकर सुनना:** शिकायत विवरण पेज पर **'Read Aloud'** बटन दबाकर पूरा आवेदन या अधिकारी की टिप्पणी सुनें।\n"
                "• **AI वॉइस मोड:** इस असिस्टेंट में **'Voice Mode'** चालू करके सभी उत्तर सीधे आवाज़ में सुनें।\n"
                "• **ऑडियो नियंत्रण:** ऑडियो को बीच में **Play**, **Pause** या **Stop** करने के लिए प्लेयर कंट्रोल्स का उपयोग करें।\n"
                "• **भाषाएं:** यह सुविधा **अंग्रेजी और हिंदी** दोनों भाषाओं में उपलब्ध है।"
            )
        },
        'suggested_actions': {
            'en-IN': ["Toggle Voice Mode", "Create Complaint with Voice", "Help & Support"],
            'hi-IN': ["वॉइस मोड टॉगल करें", "बोलकर शिकायत दर्ज करें", "सहायता"]
        }
    },

    'privacy_and_security': {
        'patterns': [
            r'\b(privacy|security|data\s*protection|who\s*can\s*see\s*my\s*complaint|confidential|multi\s*tenant)\b',
            r'\b(kya\s*meri\s*complaint\s*safe\s*hai|security\s*kya\s*hai)\b',
            r'(गोपनीयता|डेटा\s*सुरक्षा|क्या\s*मेरी\s*शिकायत\s*सुरक्षित\s*है|मल्टी\s*टेनेंट)'
        ],
        'replies': {
            'en-IN': (
                "**ProofVoice Privacy & Multi-Tenant Campus Isolation:**\n\n"
                "• **Strict Student Isolation:** You can only view and search your own grievances. Other students have zero access to your complaints, personal data, or room numbers.\n"
                "• **Campus-Level Boundary:** Campus administrators can only view tickets within their verified institution.\n"
                "• **Internal Notes Protection:** Administrative internal discussion notes are strictly protected and never displayed to student accounts.\n"
                "• **Password Protection:** Passwords are never stored in plain text and are securely hashed with PBKDF2-SHA256."
            ),
            'hi-IN': (
                "**गोपनीयता और डेटा सुरक्षा (Data Privacy & Security):**\n\n"
                "• **पूर्ण छात्र गोपनीयता:** आप केवल अपनी शिकायतें ही देख सकते हैं। अन्य छात्र आपकी शिकायतों या व्यक्तिगत जानकारी को नहीं देख सकते।\n"
                "• **परिसर स्तर पर अलगाव:** एक कॉलेज के अधिकारी केवल अपने ही कॉलेज की शिकायतों को देख व प्रबंधित कर सकते हैं।\n"
                "• **आंतरिक नोट्स की सुरक्षा:** एडमिन के आंतरिक नोट्स छात्रों से पूरी तरह गोपनीय रहते हैं।\n"
                "• **सुरक्षित पासवर्ड:** पासवर्ड कभी भी साधारण टेक्स्ट में स्टोर नहीं होते और PBKDF2-SHA256 से सुरक्षित रहते हैं।"
            )
        },
        'suggested_actions': {
            'en-IN': ["View My Complaints", "Profile & Settings", "Help & Support"],
            'hi-IN': ["मेरी शिकायतें देखें", "प्रोफाइल और सेटिंग्स", "सहायता"]
        }
    }
}

def match_campus_knowledge(query: str, lang: str):
    """
    Checks if query matches any ProofVoice platform workflow.
    Returns response dict strictly in English or Hindi.
    """
    if not query:
        return None

    clean_lang = 'hi-IN' if lang == 'hi-IN' else 'en-IN'

    for topic_key, topic_data in CAMPUS_KNOWLEDGE_TOPICS.items():
        patterns = topic_data['patterns']
        if any(re.search(p, query, re.IGNORECASE) for p in patterns):
            replies = topic_data['replies']
            reply_text = replies.get(clean_lang, replies['en-IN'])
            speak_text = re.sub(r'[*#_`•✓⏳\n]+', ' ', reply_text)
            speak_text = re.sub(r'https?://\S+', '', speak_text).strip()
            actions = topic_data.get('suggested_actions', {}).get(clean_lang, ["View Dashboard", "My Complaints", "Help & Support"])
            return {
                'reply': reply_text,
                'speak_text': speak_text[:300],
                'topic': f"campus_{topic_key}",
                'language': clean_lang,
                'suggested_actions': actions
            }

    return None
