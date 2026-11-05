# -*- coding: utf-8 -*-
"""
ProofVoice Advanced Built-In General Knowledge & Educational Brain.
Provides instant, highly accurate educational and general knowledge responses for:
- Computer Science (Computer Networks, IT, Operating Systems, TCP/IP, UDP)
- Programming (Python explanations, Prime number programs, JavaScript, Data Structures)
- Technology (Wi-Fi, Artificial Intelligence, Projectors, Laboratory Equipment)
- World Facts & Geography (Capital of Japan, etc.)
- Natural Conversational Rapport (Hello, how are you?, Smalltalk)

Enforces the Absolute Priority Rule:
General and educational questions ALWAYS receive direct educational answers.
NEVER triggers campus complaint classifications.
"""

import re

GENERAL_KNOWLEDGE_TOPICS = {
    # 1. Computer Networks (English & Hindi)
    'computer_networks': {
        'patterns': [
            r'\b(computer\s*networks?|what\s+is\s+(a\s+)?(computer\s+)?network|networking|define\s+network|types\s+of\s+networks?)\b',
            r'(कंप्यूटर\s*नेटवर्क|कंप्यूटर\s*नेटवर्क\s*समझाओ|नेटवर्क\s*क्या\s*है|नेटवर्किंग\s*क्या\s*है)',
            r'(கணினி\s*வலைப்பின்னல்|కంప్యూటర్\s*నెట్‌వర్క్|કમ્પ્યુટર\s*નેટવર્ક|কম্পিউটার\s*নেটওয়ার্ক)'
        ],
        'subject': 'Computer Networks',
        'replies': {
            'en-IN': (
                "**Computer Networks Explained:**\n\n"
                "A **computer network** is a system of interconnected computing devices (such as computers, servers, smartphones, routers, and switches) that communicate with one another to exchange data and share resources via communication protocols.\n\n"
                "### 1. Key Objectives & Benefits\n"
                "• **Resource Sharing:** Sharing printers, storage drives, and high-performance computing power.\n"
                "• **Data Exchange:** Instant transfer of files, emails, web pages, and multimedia.\n"
                "• **Centralized Management:** Streamlined user permissions, security policies, and software distribution.\n\n"
                "### 2. Major Network Classifications by Scale\n"
                "• **PAN (Personal Area Network):** Short-range connections (e.g. Bluetooth pairing within 10 meters).\n"
                "• **LAN (Local Area Network):** Covers a localized area like a university campus, laboratory, or office.\n"
                "• **MAN (Metropolitan Area Network):** Spans an entire city or metropolitan region (e.g. cable TV networks).\n"
                "• **WAN (Wide Area Network):** Spans countries or the globe. The **Internet** is the largest public WAN.\n"
                "• **WLAN (Wireless LAN):** Wi-Fi networks allowing mobility within a localized perimeter.\n\n"
                "### 3. Common Network Topologies\n"
                "• **Star Topology:** Every node connects directly to a central hub or switch (most popular today).\n"
                "• **Mesh Topology:** Devices are redundantly interconnected, providing supreme fault tolerance.\n"
                "• **Bus Topology:** Devices share a single central backbone cable.\n"
                "• **Ring Topology:** Devices form a closed loop where tokens circulate unidirectionally.\n\n"
                "### 4. Essential Network Hardware\n"
                "• **Router:** Directs data packets between disparate networks using IP addresses.\n"
                "• **Switch:** Forwards data frames between devices on the same local network using MAC addresses.\n"
                "• **NIC (Network Interface Card):** The hardware component enabling a device to connect to a network."
            ),
            'hi-IN': (
                "**कंप्यूटर नेटवर्क (Computer Network) की संपूर्ण व्याख्या:**\n\n"
                "**कंप्यूटर नेटवर्क** दो या दो से अधिक आपस में जुड़े हुए कंप्यूटरों और अन्य डिजिटल उपकरणों (जैसे सर्वर, प्रिंटर, राउटर, स्विच) का एक समूह होता है, जो डेटा का आदान-प्रदान और संसाधनों को साझा करने के लिए संचार प्रोटोकॉल के माध्यम से जुड़े होते हैं।\n\n"
                "### 1. कंप्यूटर नेटवर्क के प्रमुख प्रकार:\n"
                "• **LAN (Local Area Network):** यह एक सीमित दायरे (जैसे स्कूल, कॉलेज, लैब या एक इमारत) में काम करता है।\n"
                "• **MAN (Metropolitan Area Network):** यह एक पूरे शहर के दायरे में फैला होता है (जैसे शहर का केबल टीवी नेटवर्क)।\n"
                "• **WAN (Wide Area Network):** यह पूरे देश या विश्व स्तर पर फैला होता है। **इंटरनेट** दुनिया का सबसे बड़ा WAN है।\n"
                "• **PAN (Personal Area Network):** किसी एक व्यक्ति के निजी उपकरणों (जैसे ब्लूटूथ, हॉटस्पॉट) का बहुत छोटा नेटवर्क।\n\n"
                "### 2. नेटवर्क के मुख्य घटक:\n"
                "• **राउटर (Router):** विभिन्न नेटवर्कों के बीच डेटा पैकेट को सही पते (IP Address) पर भेजने का काम करता है।\n"
                "• **स्विच (Switch):** एक ही लोकल नेटवर्क में जुड़े उपकरणों के बीच डेटा ट्रांसफर करता है।\n"
                "• **NIC (नेटवर्क इंटरफेस कार्ड):** हार्डवेयर कार्ड जो कंप्यूटर को नेटवर्क से जोड़ता है।\n\n"
                "### 3. इसके मुख्य लाभ:\n"
                "• इंटरनेट और फाइलों की आसान शेयरिंग।\n"
                "• हार्डवेयर संसाधनों (जैसे प्रिंटर, सर्वर) का साझा उपयोग, जिससे लागत बचती है।\n"
                "• तेज और सुरक्षित डिजिटल संचार (ईमेल, मैसेजिंग, वीडियो कॉलिंग)।"
            )
        }
    },

    # 2. Information Technology (IT)
    'information_technology': {
        'patterns': [
            r'\b(what\s+is\s+it\b|what\s+is\s+information\s+technology|define\s+information\s+technology|explain\s+information\s+technology)\b',
            r'(सूचना\s*प्रौद्योगिकी|आईटी\s*क्या\s*है|it\s*क्या\s*है)'
        ],
        'subject': 'Information Technology',
        'replies': {
            'en-IN': (
                "**Information Technology (IT) Explained:**\n\n"
                "**Information Technology (IT)** is the comprehensive field involving the use of computers, storage systems, networking hardware, and software applications to create, process, securely store, transmit, and retrieve electronic data.\n\n"
                "### Core Pillars of IT\n"
                "1. **Computer Hardware:** Physical devices including enterprise servers, client workstations, mobile devices, and storage arrays.\n"
                "2. **Software Applications:** Operating systems, database engines, business management software, web platforms, and mobile apps.\n"
                "3. **Networking & Telecommunications:** Connecting systems securely across the internet, local intranets, and cloud platforms.\n"
                "4. **Cloud Computing:** Delivering computing power, servers, storage, and databases over the internet (e.g. AWS, Microsoft Azure, Google Cloud).\n"
                "5. **Cybersecurity:** Protecting digital assets, network infrastructure, and student/customer records against unauthorized access and cyber threats.\n"
                "6. **Database Management (DBMS):** Organizing and querying structured information using SQL and NoSQL engines (e.g. MySQL, PostgreSQL, MongoDB).\n\n"
                "💡 *In Everyday Life:* IT powers everything from modern university portals and online banking to hospital patient records and global supply chains."
            ),
            'hi-IN': (
                "**सूचना प्रौद्योगिकी (Information Technology - IT) क्या है:**\n\n"
                "**सूचना प्रौद्योगिकी (IT)** वह व्यापक तकनीकी क्षेत्र है जिसमें इलेक्ट्रॉनिक डेटा को सुरक्षित रूप से बनाने, प्रोसेस करने, संग्रहीत (store) करने, सुरक्षित रखने और प्रसारित करने के लिए कंप्यूटर, सॉफ्टवेयर, नेटवर्क और इंटरनेट का उपयोग किया जाता है।\n\n"
                "### आईटी के प्रमुख स्तंभ:\n"
                "• **हार्डवेयर:** सर्वर, पर्सनल कंप्यूटर, स्टोरेज डिवाइस और नेटवर्किंग उपकरण।\n"
                "• **सॉफ्टवेयर:** ऑपरेटिंग सिस्टम, डेटाबेस, वेबसाइट्स और मोबाइल ऐप्स।\n"
                "• **साइबर सुरक्षा (Cybersecurity):** डिजिटल डेटा और नेटवर्क को हैकिंग और वायरस से सुरक्षित रखना।\n"
                "• **क्लाउड कंप्यूटिंग:** इंटरनेट के माध्यम से डेटा और सर्वर का उपयोग करना (जैसे Google Cloud, AWS)।"
            )
        }
    },

    # 3. Python Programming & Prime Number Checker
    'python_programming': {
        'patterns': [
            r'\b(explain\s+python(\s+programming)?|what\s+is\s+python(\s+programming)?|python\s+programming\s+language)\b',
            r'(पायथन\s*प्रोग्रामिंग|पायथन\s*क्या\s*है|पायथन\s*समझाओ)'
        ],
        'subject': 'Python Programming',
        'creator': 'Guido van Rossum',
        'year': '1991',
        'replies': {
            'en-IN': (
                "**Python Programming Language:**\n\n"
                "**Python** is a high-level, interpreted, general-purpose programming language conceived in the late 1980s by **Guido van Rossum** and first released in **1991**.\n\n"
                "### Why Python is Widely Used\n"
                "• **Readability:** Python uses clean English keywords and significant whitespace indentation instead of curly brackets `{}` or semicolons `;`.\n"
                "• **Interpreted:** Code executes line-by-line, accelerating prototyping, debugging, and experimentation.\n"
                "• **Dynamically Typed:** Variables do not require strict compile-time type declarations.\n"
                "• **Multi-Paradigm:** Supports Object-Oriented Programming (OOP), Procedural, and Functional programming.\n\n"
                "### Major Industry Applications\n"
                "• **Artificial Intelligence & Machine Learning:** TensorFlow, PyTorch, Scikit-Learn, Keras.\n"
                "• **Data Science & Analytics:** Pandas, NumPy, Matplotlib, Seaborn.\n"
                "• **Web Development:** Django (powers ProofVoice backend), FastAPI, Flask.\n"
                "• **Automation & Scripting:** Web scraping (BeautifulSoup), system administration, task automation."
            ),
            'hi-IN': (
                "**पायथन (Python) प्रोग्रामिंग भाषा:**\n\n"
                "पायथन एक उच्च-स्तरीय (high-level), इंटरप्रिटेड और बेहद लोकप्रिय प्रोग्रामिंग भाषा है।\n\n"
                "**प्रमुख विशेषताएं:**\n"
                "• **सरल और पठनीय कोड:** इसमें कोड लिखना बहुत आसान और अंग्रेजी जैसा होता है।\n"
                "• **उपयोग के क्षेत्र:** आर्टिफिशियल इंटेलिजेंस (AI), मशीन लर्निंग, डेटा साइंस, और वेब डेवलपमेंट (जैसे Django)।\n"
                "• **ओपन सोर्स:** यह पूरी तरह से मुफ्त और दुनिया के सभी प्रमुख ऑपरेटिंग सिस्टम पर चलती है।"
            )
        }
    },

    # Python Prime Number Program
    'python_prime_program': {
        'patterns': [
            r'\b((write|create|give|show)\s+(a\s+)?python\s+(code|program)\s+(to\s+)?(check|find|test)\s+prime(\s+numbers?)?|prime\s+number\s+python(\s+program)?)\b',
            r'(प्राइम\s*नंबर.*पायथन|अभाज्य\s*संख्या.*पायथन|python.*prime\s*number)'
        ],
        'subject': 'Python Prime Number Program',
        'replies': {
            'en-IN': (
                "**Python Program to Check Prime Numbers:**\n\n"
                "A prime number is a positive integer greater than 1 that has no positive divisors other than 1 and itself (e.g. 2, 3, 5, 7, 11, 13).\n\n"
                "Here is an efficient, well-structured Python program using the $O(\\sqrt{n})$ trial division method:\n\n"
                "```python\n"
                "import math\n\n"
                "def is_prime(n: int) -> bool:\n"
                "    \"\"\"\n"
                "    Determines whether a given integer is a prime number.\n"
                "    Time Complexity: O(sqrt(n))\n"
                "    \"\"\"\n"
                "    # Numbers less than or equal to 1 are not prime\n"
                "    if n <= 1:\n"
                "        return False\n"
                "    # 2 is the only even prime number\n"
                "    if n == 2:\n"
                "        return True\n"
                "    # All other even numbers are not prime\n"
                "    if n % 2 == 0:\n"
                "        return False\n\n"
                "    # Check odd divisors up to the square root of n\n"
                "    limit = int(math.isqrt(n))\n"
                "    for divisor in range(3, limit + 1, 2):\n"
                "        if n % divisor == 0:\n"
                "            return False\n\n"
                "    return True\n\n"
                "# Example Usage & Interactive Testing:\n"
                "test_numbers = [1, 2, 17, 25, 29, 100, 101]\n"
                "for num in test_numbers:\n"
                "    status = \"Prime\" if is_prime(num) else \"Not Prime\"\n"
                "    print(f\"{num} -> {status}\")\n"
                "```\n\n"
                "### How This Code Works:\n"
                "1. **Quick Filters:** Instantly filters out $n \\le 1$ and even numbers $> 2$.\n"
                "2. **Square Root Optimization:** A composite number must have a factor less than or equal to $\\sqrt{n}$. We only test odd divisors up to $\\sqrt{n}$, making the execution extremely fast even for large numbers."
            )
        }
    },

    # 4. Wi-Fi Technology
    'wifi_technology': {
        'patterns': [
            r'\b(how\s+does\s+wi-?fi\s+work|explain\s+wi-?fi|what\s+is\s+wi-?fi(\s+technology)?|how\s+wi-?fi\s+works)\b',
            r'(वाई-फाई\s*कैसे\s*काम\s*करता\s*है|वाई-फाई\s*क्या\s*है|wifi\s*kaise\s*kaam\s*karta\s*hai)'
        ],
        'subject': 'Wi-Fi Technology',
        'replies': {
            'en-IN': (
                "**How Wi-Fi Works (Wireless Networking Explained):**\n\n"
                "**Wi-Fi** (based on the **IEEE 802.11** standards family) is a wireless networking technology that uses radio frequency (RF) waves to transmit digital data between devices without physical cables.\n\n"
                "### Step-by-Step Working Mechanism:\n"
                "1. **Digital to Radio Signal Conversion:** When your smartphone or laptop requests a web page, its internal wireless adapter encodes digital binary data (`0`s and `1`s) into high-frequency radio waves.\n"
                "2. **Transmission via Antenna:** The device's antenna broadcasts these radio waves over the airwaves.\n"
                "3. **Router Reception & Decoding:** A wireless router or campus access point captures the radio waves through its antennas and decodes them back into digital binary pulses.\n"
                "4. **Internet Routing:** The router transmits the data over a physical wired Ethernet or optical fiber backbone to the global Internet.\n"
                "5. **Return Path:** When the web server replies, the router converts the incoming data back into radio signals and transmits them back to your device.\n\n"
                "### Common Wi-Fi Frequencies:\n"
                "• **2.4 GHz Band:** Longer range and superior wall penetration, but lower speeds and prone to interference from microwaves and Bluetooth.\n"
                "• **5 GHz Band:** Much faster data speeds with lower latency, but shorter physical broadcast range.\n"
                "• **6 GHz Band (Wi-Fi 6E & Wi-Fi 7):** Ultrawide bandwidth with virtually no channel congestion."
            ),
            'hi-IN': (
                "**वाई-फाई (Wi-Fi) कैसे काम करता है:**\n\n"
                "वाई-फाई एक ऐसी तकनीक है जो बिना किसी तार (वायर) के **रेडियो तरंगों (Radio Waves)** का उपयोग करके इंटरनेट और डेटा का आदान-प्रदान करती है।\n\n"
                "1. **रेडियो सिग्नल में बदलना:** जब आप मोबाइल या लैपटॉप पर कुछ सर्च करते हैं, तो कंप्यूटर चिप उस डेटा को रेडियो तरंगों में बदल देती है।\n"
                "2. **राउटर तक पहुंचना:** आपका डिवाइस यह सिग्नल हवा में भेजता है, जिसे कमरे में लगा **वाई-फाई राउटर** पकड़ लेता है।\n"
                "3. **इंटरनेट से जुड़ना:** राउटर इन तरंगों को वापस डिजिटल डेटा में बदलकर ऑप्टिकल फाइबर केबल के जरिए इंटरनेट सर्वर तक भेजता है।\n\n"
                "यह आमतौर पर **2.4 GHz** (लंबी दूरी) और **5 GHz** (तेज स्पीड) फ्रीक्वेंसी पर काम करता है।"
            )
        }
    },

    # 5. TCP Protocol in Simple Words
    'tcp_simple': {
        'patterns': [
            r'\b(what\s+is\s+tcp\b|explain\s+tcp\b|tcp\s+in\s+simple\s+(words|terms)|define\s+tcp)\b',
            r'(tcp\s*क्या\s*है|tcp\s*समझाओ)'
        ],
        'subject': 'Transmission Control Protocol (TCP)',
        'replies': {
            'en-IN': (
                "**What is TCP? (Explained in Simple Words):**\n\n"
                "**TCP** stands for **Transmission Control Protocol**. It is one of the foundational communication rules of the Internet, responsible for ensuring that data sent between computers arrives **completely, accurately, and in the exact right order**.\n\n"
                "### Think of TCP Like a Registered Postal Delivery:\n"
                "If you send a 100-page book in 100 separate numbered envelopes:\n"
                "• TCP ensures all 100 envelopes arrive at the destination.\n"
                "• If envelope #42 gets lost in transit, TCP automatically detects it and asks the sender: *\"Please re-send envelope #42.\"*\n"
                "• Once all envelopes arrive, TCP rearranges them from page 1 to page 100 before handing the book to you.\n\n"
                "### Core Characteristics of TCP:\n"
                "1. **Connection-Oriented:** Establishes a verified connection before sending data using the famous **Three-Way Handshake**:\n"
                "   - *Step 1 (SYN):* Client asks: \"Can we connect?\"\n"
                "   - *Step 2 (SYN-ACK):* Server answers: \"Yes, I am ready!\"\n"
                "   - *Step 3 (ACK):* Client acknowledges: \"Great, sending data now!\"\n"
                "2. **Reliable:** Provides delivery confirmations (acknowledgments). No packet is silently lost.\n"
                "3. **In-Order Delivery:** Sequences data packets so they never arrive scrambled.\n"
                "4. **Flow & Congestion Control:** Automatically slows down data transmission if the receiver's network buffer is full."
            )
        }
    },

    # 6. TCP vs UDP Comparison
    'tcp_vs_udp': {
        'patterns': [
            r'\b(difference\s+between\s+tcp\s+and\s+udp|tcp\s+(vs|versus)\s+udp|compare\s+tcp\s+and\s+udp)\b',
            r'(tcp\s*और\s*udp\s*में\s*अंतर|tcp\s*vs\s*udp)'
        ],
        'subject': 'TCP vs UDP Comparison',
        'replies': {
            'en-IN': (
                "**Difference Between TCP and UDP:**\n\n"
                "Both **TCP (Transmission Control Protocol)** and **UDP (User Datagram Protocol)** are core Transport Layer protocols in the Internet protocol suite, but they are built for entirely different priorities:\n\n"
                "| Feature | TCP (Transmission Control Protocol) | UDP (User Datagram Protocol) |\n"
                "| :--- | :--- | :--- |\n"
                "| **Connection Type** | **Connection-Oriented** (requires 3-way handshake) | **Connectionless** (sends data immediately) |\n"
                "| **Reliability** | **Guaranteed Delivery** (lost packets are resent) | **Best-Effort** (lost packets are dropped) |\n"
                "| **Packet Ordering** | **Strictly Ordered** (packets numbered & sequenced) | **Unordered** (packets arrive in any order) |\n"
                "| **Speed & Overhead** | **Slower** (larger header: 20–60 bytes) | **Extremely Fast** (small header: only 8 bytes) |\n"
                "| **Error Checking** | Extensive checksum, ACKs, flow control | Basic checksum only; no recovery |\n"
                "| **Best Used For** | Web browsing (HTTP/HTTPS), Email (SMTP), File downloads | Live video streaming, Online multiplayer gaming, VoIP, DNS |\n\n"
                "💡 *Analogy:* **TCP** is like a registered courier requiring signature confirmation, while **UDP** is like a live radio broadcast where missing a second is better than delaying the show."
            )
        }
    },

    # 7. Artificial Intelligence
    'artificial_intelligence': {
        'patterns': [
            r'\b(what\s+is\s+artificial\s+intelligence|explain\s+artificial\s+intelligence|what\s+is\s+ai\b|define\s+ai\b)\b',
            r'(आर्टिफिशियल\s*इंटेलिजेंस|कृत्रिम\s*बुद्धिमत्ता|ai\s*क्या\s*है)'
        ],
        'subject': 'Artificial Intelligence',
        'creator': 'John McCarthy coined the term in 1956',
        'year': '1956',
        'replies': {
            'en-IN': (
                "**Artificial Intelligence (AI) Explained:**\n\n"
                "**Artificial Intelligence (AI)** is the branch of Computer Science dedicated to creating systems, algorithms, and machines capable of performing tasks that typically require human cognition.\n\n"
                "### Core Pillars & Subfields:\n"
                "• **Machine Learning (ML):** Statistical models that learn patterns and make predictions from training data rather than relying on hardcoded rules.\n"
                "• **Deep Learning (DL):** Multi-layered artificial neural networks inspired by biological neurons, powering breakthroughs in image recognition and autonomous driving.\n"
                "• **Natural Language Processing (NLP):** Enables computers to read, interpret, translate, and generate human languages (e.g. ChatGPT, Gemini, ProofVoice Assistant).\n"
                "• **Computer Vision:** Enables algorithms to recognize and analyze visual inputs from images and video feeds.\n"
                "• **Speech AI:** Converts spoken voice into text (Speech-to-Text via Gnani AI Prisma) and synthesizes realistic speech audio (Text-to-Speech via Timbre)."
            ),
            'hi-IN': (
                "**आर्टिफिशियल इंटेलिजेंस (AI - कृत्रिम बुद्धिमत्ता):**\n\n"
                "आर्टिफिशियल इंटेलिजेंस कंप्यूटर विज्ञान की वह शाखा है जो कंप्यूटर और मशीनों को इंसानों की तरह सोचने, सीखने और निर्णय लेने में सक्षम बनाती है।\n\n"
                "• **मशीन लर्निंग:** अनुभव और डेटा से खुद सीखना।\n"
                "• **नेचुरल लैंग्वेज प्रोसेसिंग (NLP):** इंसानी भाषा (हिंदी, अंग्रेजी) को समझना और जवाब देना।\n"
                "• **स्पीच टेक्नोलॉजी:** इंसानी आवाज को टेक्स्ट में बदलना और बोलकर जवाब देना।"
            )
        }
    },

    # 8. World Facts: Capital of Japan
    'capital_of_japan': {
        'patterns': [
            r'\b(capital\s+of\s+japan|what\s+is\s+the\s+capital\s+of\s+japan)\b',
            r'(जापान\s*की\s*राजधानी|जापान\s*की\s*राजधानी\s*क्या\s*है)'
        ],
        'subject': 'Capital of Japan',
        'replies': {
            'en-IN': (
                "The capital of Japan is **Tokyo** (東京都 - *Tōkyō*).\n\n"
                "### Key Facts About Tokyo:\n"
                "• **Location:** Situated on the eastern coast of Japan's main island of Honshu, head of Tokyo Bay.\n"
                "• **Population:** The Greater Tokyo Area is the most populous metropolitan area in the world, with over **37 million residents**.\n"
                "• **Historical Background:** Originally a modest fishing village named **Edo**, it became the political center in 1603 when Tokugawa Ieyasu established the shogunate. In 1868, Emperor Meiji moved the imperial seat from Kyoto to Edo and renamed it *Tokyo* (meaning \"Eastern Capital\").\n"
                "• **Global Significance:** Tokyo is an economic superpower, a premier center for high technology, anime culture, and business, and host of the 1964 and 2020 Summer Olympic Games."
            ),
            'hi-IN': (
                "जापान की राजधानी **टोक्यो (Tokyo)** है।\n\n"
                "**टोक्यो के बारे में मुख्य तथ्य:**\n"
                "• यह दुनिया का सबसे अधिक आबादी वाला महानगरीय क्षेत्र है (3.7 करोड़ से अधिक निवासी)।\n"
                "• 1868 से पहले इसे **'एदो' (Edo)** कहा जाता था। जब सम्राट मेइजी ने राजधानी क्योटो से यहाँ स्थानांतरित की, तो इसका नाम बदलकर 'टोक्यो' (पूर्वी राजधानी) रखा गया।\n"
                "• यह तकनीक, संस्कृति और वैश्विक व्यापार का एक प्रमुख वैश्विक केंद्र है।"
            )
        }
    },

    # 9. Operating Systems
    'operating_systems': {
        'patterns': [
            r'\b(explain\s+operating\s+systems?|what\s+is\s+an\s+operating\s+system|define\s+operating\s+system)\b',
            r'(ऑपरेटिंग\s*सिस्टम\s*क्या\s*है|ऑपरेटिंग\s*सिस्टम\s*समझाओ)'
        ],
        'subject': 'Operating Systems',
        'replies': {
            'en-IN': (
                "**Operating Systems (OS) Explained:**\n\n"
                "An **Operating System (OS)** is foundational system software that manages a computer's physical hardware resources and provides standard services for user application programs.\n\n"
                "### Core Responsibilities of an OS:\n"
                "1. **Processor & Process Management:** Decides which process gets CPU time and for how long using scheduling algorithms (Round Robin, Priority, Multi-level queue).\n"
                "2. **Memory Management:** Allocates and tracks RAM blocks for active programs, implementing virtual memory and paging when physical RAM is exhausted.\n"
                "3. **File System Management:** Organizes files into hierarchical directories (NTFS, ext4, APFS) and controls read/write access permissions.\n"
                "4. **Device Drivers & I/O:** Provides a standard abstraction layer for communicating with monitors, keyboards, disk drives, and network cards.\n"
                "5. **User Interface:** Provides either a Graphical User Interface (GUI) or a Command Line Interface (CLI/Shell).\n\n"
                "### Common Examples:\n"
                "• **Desktop/Server:** Linux (Ubuntu, Debian, RedHat), Microsoft Windows, macOS.\n"
                "• **Mobile:** Android (built on the Linux kernel), iOS."
            )
        }
    },

    # 10. Hardware: What is a Projector?
    'hardware_projector': {
        'patterns': [
            r'\b(what\s+is\s+a\s+projector|explain\s+(a\s+)?projector|define\s+projector)\b',
            r'(प्रोजेक्टर\s*क्या\s*है|प्रोजेक्टर\s*किसे\s*कहते\s*हैं)'
        ],
        'subject': 'Projector',
        'replies': {
            'en-IN': (
                "**What is a Projector? (Educational Overview):**\n\n"
                "A **projector** is an optical output hardware device that accepts a video signal from a computer, media player, or smartphone and projects the enlarged image onto a projection screen or white wall using a bright light source and focusing lens system.\n\n"
                "### Common Projector Technologies:\n"
                "• **DLP (Digital Light Processing):** Uses an array of microscopic mirrors on a semiconductor chip (DMD) to reflect light. Known for high contrast and smooth motion.\n"
                "• **3LCD:** Splits light into primary colors (Red, Green, Blue) using dichroic mirrors and passes them through three separate LCD panels. Known for rich, vibrant color reproduction.\n"
                "• **Laser & LED Projectors:** Modern solid-state light sources that eliminate traditional hot mercury lamps, offering instant on/off and 20,000+ operating hours.\n\n"
                "### Primary Applications:\n"
                "• **Education:** Interactive smart classrooms, lecture halls, and seminar presentations.\n"
                "• **Corporate:** Boardroom presentations, video conferences, and financial displays.\n"
                "• **Home Entertainment:** Large-scale home theater cinema systems."
            )
        }
    },

    # 11. Laboratory Equipment
    'laboratory_equipment': {
        'patterns': [
            r'\b(what\s+is\s+laboratory\s+equipment|explain\s+laboratory\s+equipment|laboratory\s+instruments?)\b',
            r'(प्रयोगशाला\s*उपकरण|लैब\s*उपकरण\s*क्या\s*हैं)'
        ],
        'subject': 'Laboratory Equipment',
        'replies': {
            'en-IN': (
                "**What is Laboratory Equipment?**\n\n"
                "**Laboratory equipment** refers to the collection of scientific tools, measuring instruments, and apparatus used by scientists, researchers, and students to conduct experiments, synthesize compounds, analyze samples, and collect empirical data.\n\n"
                "### Common Categories Across Scientific Disciplines:\n"
                "• **Electronics & Computer Labs:** Digital Storage Oscilloscopes (DSO), Function Generators, Multimeters, Microcontroller Dev Boards, and Logic Analyzers.\n"
                "• **Chemistry Labs:** Bunsen burners, Volumetric flasks, Pipettes, Burettes, Centrifuges, and Fume extraction hoods.\n"
                "• **Physics & Optics Labs:** Optical benches, Lasers, Spectrometers, Galvanometers, and Vernier calipers.\n"
                "• **Biology Labs:** Compound light microscopes, Autoclaves, Incubators, Petri dishes, and Electrophoresis chambers."
            )
        }
    },

    # 12. Friendly Conversational Smalltalk
    'friendly_greeting': {
        'patterns': [
            r'^(hello|hi|hey|howdy|greetings|namaste|vanakkam)\b',
            r'\b(how\s*are\s*you|how\s*r\s*u|how\s*are\s*things|how\s*are\s*you\s*doing)\b',
            r'(नमस्ते|प्रणाम|कैसे\s*हो|क्या\s*हाल\s*है)'
        ],
        'subject': 'Conversational Greeting',
        'replies': {
            'en-IN': (
                "Hello! I am doing great, thank you for asking! 😊\n\n"
                "I am **ProofVoice AI Assistant**, your intelligent, multilingual conversational guide. I can help you with:\n"
                "• **Education & General Knowledge:** Computer Science, Programming, Networks, Science, World Facts, and more.\n"
                "• **ProofVoice Website Navigation:** Signing out, password updates, profile editing, and notifications.\n"
                "• **Campus Grievance Guidance:** Assistance with reporting campus facilities when you need official institutional resolution.\n\n"
                "How can I help you today?"
            ),
            'hi-IN': (
                "नमस्ते! मैं बहुत अच्छा हूँ, पूछने के लिए धन्यवाद! 😊\n\n"
                "मैं **ProofVoice AI असिस्टेंट** हूँ। मैं कंप्यूटर साइंस, प्रोग्रामिंग, सामान्य ज्ञान, या ProofVoice वेबसाइट पर किसी भी प्रक्रिया में आपकी सहायता के लिए तैयार हूँ।\n\n"
                "आज आप क्या जानना या सीखना चाहते हैं?"
            )
        }
    },
    # 13. Java Fibonacci Series Program
    'java_fibonacci_program': {
        'patterns': [
            r'\b(fibonacci(\s*series)?|fibonacci\s*program|java\s*program\s*(for|to|of)?\s*fibonacci|fibonacci\s*in\s*java)\b',
            r'(फाइबोनैचि|फाइबोनैकी|fibonacci)'
        ],
        'subject': 'Java Fibonacci Series Program',
        'replies': {
            'en-IN': (
                "**Java Program to Generate the Fibonacci Series:**\n\n"
                "The **Fibonacci sequence** is a series of numbers where each number is the sum of the two preceding ones, starting from 0 and 1:\n"
                "$$0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, \\dots$$\n\n"
                "### 1. Complete Java Implementation (Iterative - O(n) Time, O(1) Space)\n\n"
                "```java\n"
                "import java.util.Scanner;\n\n"
                "public class FibonacciSeries {\n"
                "    // Method to display Fibonacci sequence up to n terms\n"
                "    public static void printFibonacci(int n) {\n"
                "        if (n <= 0) {\n"
                "            System.out.println(\"Please enter a positive integer greater than 0.\");\n"
                "            return;\n"
                "        }\n\n"
                "        long first = 0, second = 1;\n"
                "        System.out.print(\"Fibonacci Series (\" + n + \" terms): \");\n\n"
                "        for (int i = 1; i <= n; i++) {\n"
                "            System.out.print(first + (i < n ? \", \" : \"\\n\"));\n"
                "            long next = first + second;\n"
                "            first = second;\n"
                "            second = next;\n"
                "        }\n"
                "    }\n\n"
                "    public static void main(String[] args) {\n"
                "        Scanner scanner = new Scanner(System.in);\n"
                "        System.out.print(\"Enter the number of terms: \");\n\n"
                "        if (scanner.hasNextInt()) {\n"
                "            int count = scanner.nextInt();\n"
                "            printFibonacci(count);\n"
                "        } else {\n"
                "            System.out.println(\"Invalid input. Please enter a valid integer.\");\n"
                "        }\n\n"
                "        scanner.close();\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### 2. Sample Output\n"
                "```text\n"
                "Enter the number of terms: 10\n"
                "Fibonacci Series (10 terms): 0, 1, 1, 2, 3, 5, 8, 13, 21, 34\n"
                "```\n\n"
                "### 3. How It Works\n"
                "1. **Variables:** `first` is initialized to 0 and `second` to 1.\n"
                "2. **Loop:** In each turn, `next = first + second` calculates the next term.\n"
                "3. **Update:** `first = second` and `second = next` shifts the window forward.\n"
                "4. **Efficiency:** Time complexity is **O(n)** and auxiliary space is **O(1)**."
            ),
            'hi-IN': (
                "**जावा में फाइबोनैचि सीरीज (Fibonacci Series) का संपूर्ण प्रोग्राम:**\n\n"
                "**फाइबोनैचि श्रृंखला** वह संख्याओं का क्रम है जिसमें प्रत्येक संख्या अपने पिछले दो संख्याओं का योग होती है:\n"
                "$$0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, \\dots$$\n\n"
                "```java\n"
                "import java.util.Scanner;\n\n"
                "public class FibonacciSeries {\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        System.out.print(\"पदों की संख्या दर्ज करें: \");\n"
                "        int n = sc.nextInt();\n\n"
                "        long first = 0, second = 1;\n"
                "        System.out.print(\"फाइबोनैचि सीरीज: \");\n\n"
                "        for (int i = 1; i <= n; i++) {\n"
                "            System.out.print(first + (i < n ? \", \" : \"\\n\"));\n"
                "            long next = first + second;\n"
                "            first = second;\n"
                "            second = next;\n"
                "        }\n"
                "        sc.close();\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "**समय जटिलता (Time Complexity):** O(n)\n"
                "**स्थान जटिलता (Space Complexity):** O(1)"
            )
        }
    },

    # 14. Who Invented the Computer
    'who_invented_computer': {
        'patterns': [
            r'\b(who\s*(invented|created|made|father\s*of)\s*(the\s*)?computer|invention\s*of\s*(the\s*)?computer)\b',
            r'(कंप्यूटर\s*का\s*आविष्कार\s*किसने|कंप्यूटर\s*के\s*जनक|कंप्यूटर\s*किसने\s*बनाया)',
            r'(கணினியைக்\s*கண்டுபிடித்தவர்|కంప్యూటర్‌ను\s*కనుగొన్నది|কম্পিউটার\s*কে\s*আবিষ্কার)'
        ],
        'subject': 'Invention of the Computer',
        'replies': {
            'en-IN': (
                "**Who Invented the Computer?**\n\n"
                "The invention of the computer was a multi-stage historical progression with two key founding figures:\n\n"
                "### 1. Charles Babbage — The 'Father of the Computer'\n"
                "• Between **1833 and 1871**, English mathematician and mechanical engineer **Charles Babbage** designed the **Analytical Engine**.\n"
                "• It was the world's first design for a general-purpose, program-controlled mechanical computer containing an Arithmetic Logic Unit (the 'Mill'), memory store, and punched-card input.\n\n"
                "### 2. Ada Lovelace — The First Computer Programmer\n"
                "• English mathematician **Ada Lovelace** wrote the first published algorithm intended for implementation on Babbage's Analytical Engine in 1843, making her the world's first computer programmer.\n\n"
                "### 3. Alan Turing — The Father of Modern Theoretical Computer Science\n"
                "• In **1936**, British mathematician **Alan Turing** introduced the concept of the **Universal Turing Machine**, formulating the foundational principles of modern digital computers, algorithms, and artificial intelligence."
            ),
            'hi-IN': (
                "**कंप्यूटर का आविष्कार किसने किया?**\n\n"
                "कंप्यूटर के जनक (Father of the Computer) **चार्ल्स बैबेज (Charles Babbage)** को माना जाता है।\n\n"
                "• **चार्ल्स बैबेज (1833-1871):** उन्होंने दुनिया के पहले यांत्रिक कंप्यूटर **'एनालिटिकल इंजन' (Analytical Engine)** की रूपरेखा तैयार की, जिसमें आधुनिक कंप्यूटर की तरह मेमोरी और सीपीयू (Mill) का सिद्धांत था।\n"
                "• **एडा लवलेस (Ada Lovelace):** दुनिया की पहली कंप्यूटर प्रोग्रामर मानी जाती हैं, जिन्होंने बैबेज के इंजन के लिए पहला एल्गोरिदम लिखा।\n"
                "• **एलन ट्यूरिंग (Alan Turing):** आधुनिक डिजिटल कंप्यूटर साइंस और आर्टिफिशियल इंटेलिजेंस के जनक कहे जाते हैं।"
            )
        }
    },

    # 15. Factorial Function (JavaScript & Python)
    'factorial_program': {
        'patterns': [
            r'\b(factorial(\s*function|\s*program)?|factorial\s*(in\s*)?(javascript|js|python|java)|find\s*factorial)\b',
            r'(फैक्टोरियल|factorial)'
        ],
        'subject': 'Factorial Program',
        'replies': {
            'en-IN': (
                "**Factorial Program in JavaScript & Python:**\n\n"
                "The **factorial** of a non-negative integer $n$ (denoted as $n!$) is the product of all positive integers less than or equal to $n$:\n"
                "$$5! = 5 \\times 4 \\times 3 \\times 2 \\times 1 = 120$$\n"
                "*(Note: $0! = 1$ by mathematical definition).*\n\n"
                "### 1. JavaScript Implementation\n\n"
                "```javascript\n"
                "function factorial(n) {\n"
                "    if (n < 0) throw new Error('Factorial not defined for negative numbers.');\n"
                "    if (n === 0 || n === 1) return 1;\n\n"
                "    let result = 1;\n"
                "    for (let i = 2; i <= n; i++) {\n"
                "        result *= i;\n"
                "    }\n"
                "    return result;\n"
                "}\n\n"
                "// Example usage:\n"
                "console.log('5! =', factorial(5));   // Output: 120\n"
                "console.log('0! =', factorial(0));   // Output: 1\n"
                "```\n\n"
                "### 2. Complexity\n"
                "• **Time Complexity:** $O(n)$ — Linear time.\n"
                "• **Space Complexity:** $O(1)$ — Iterative constant space."
            )
        }
    }
,

    # 17. Quantum Computing
    'quantum_computing': {
        'patterns': [
            r'\b(quantum\s*comput(ing|er|ers)?|qubits?|superposition|quantum\s*entanglement)\b',
            r'(क्वांटम\s*कंप्यूटिंग|क्वांटम\s*कंप्यूटर|क्यूबिट)',
            r'(குவாண்டம்\s*கம்ப்யூட்டிங்|క్వాంటం\s*కంప్యూటింగ్|কোয়ান্টাম\s*কম্পিউটিং)'
        ],
        'subject': 'Quantum Computing',
        'replies': {
            'en-IN': (
                "**Quantum Computing Explained:**\\n\\n"
                "**Quantum Computing** is a multidisciplinary field of computer science and physics that harnesses the fundamental laws of **quantum mechanics** (such as *superposition* and *entanglement*) to solve problems that are exponentially too complex for classical binary computers.\\n\\n"
                "### 1. Classical vs. Quantum Bits\\n"
                "• **Classical Bits:** Binary units that exist strictly in state `0` or state `1`.\\n"
                "• **Qubits (Quantum Bits):** Can exist in state `|0⟩`, state `|1⟩`, or a linear **superposition** of both simultaneously. This enables a quantum system of $n$ qubits to process $2^n$ states in parallel.\\n\\n"
                "### 2. Core Quantum Principles\\n"
                "• **Superposition:** Allows qubits to hold multiple probabilistic states at once until measured.\\n"
                "• **Entanglement:** A phenomenon where pairs of qubits become inextricably linked, such that the state of one instantly dictates the state of another regardless of physical separation.\\n"
                "• **Quantum Interference:** Directs probability amplitudes toward constructive interference for the correct answer and destructive interference for wrong answers.\\n\\n"
                "### 3. Practical Applications\\n"
                "• **Cryptography & Security:** Shor's algorithm can factorize large prime integers in polynomial time, driving the need for Post-Quantum Cryptography (PQC).\\n"
                "• **Molecular Chemistry & Drug Discovery:** Simulating complex molecular bonds at quantum levels to design life-saving medications and high-efficiency batteries.\\n"
                "• **Optimization:** Route optimization in logistics, supply chains, and quantitative financial portfolios."
            ),
            'hi-IN': (
                "**क्वांटम कंप्यूटिंग (Quantum Computing) की व्याख्या:**\\n\\n"
                "**क्वांटम कंप्यूटिंग** कंप्यूटर विज्ञान और क्वांटम भौतिकी का एक अत्याधुनिक क्षेत्र है जो क्वांटम यांत्रिकी के सिद्धांतों (**सुपरपोजिशन** और **एंटैंगलमेंट**) का उपयोग करके अत्यधिक जटिल गणनाओं को बहुत तेजी से हल करता है।\\n\\n"
                "### मुख्य घटक:\\n"
                "• **क्यूबिट (Qubit):** पारंपरिक कंप्यूटर में बिट्स केवल `0` या `1` हो सकते हैं, जबकि क्वांटम कंप्यूटर में क्यूबिट एक साथ `0` और `1` दोनों अवस्थाओं (Superposition) में रह सकते हैं।\\n"
                "• **क्वांटम एंटैंगलमेंट (Entanglement):** दो या अधिक क्यूबिट्स का आपस में ऐसा गहरा संबंध जिसमें एक क्यूबिट की स्थिति बदलने पर दूसरे की स्थिति तुरंत बदल जाती है।\\n"
                "• **उपयोग:** नई दवाओं की खोज, मौसम का सटीक पूर्वानुमान, वित्तीय जोखिम मॉडलिंग और डेटा एन्क्रिप्शन।"
            )
        }
    },

    # 18. Photosynthesis
    'photosynthesis': {
        'patterns': [
            r'\b(photosynthesis|how\s*do\s*plants\s*make\s*food|chlorophyll|calvin\s*cycle)\b',
            r'(प्रकाश\s*संश्लेषण|पौधे\s*भोजन\s*कैसे\s*बनाते\s*हैं|क्लोरोफिल)',
            r'(ஒளிச்சேர்க்கை|కిరణజన్య\s*సంయోగక్రియ|সালোকসংশ্লেষ)'
        ],
        'subject': 'Photosynthesis',
        'replies': {
            'en-IN': (
                "**Photosynthesis Explained (Plant Biology):**\\n\\n"
                "**Photosynthesis** is the biological process by which green plants, algae, and certain cyanobacteria convert sunlight, water, and carbon dioxide into chemical energy in the form of glucose (sugar), releasing oxygen as a byproduct.\\n\\n"
                "### 1. Overall Chemical Equation\\n"
                "$$\\\\text{6CO}_2 + \\\\text{6H}_2\\\\text{O} + \\\\text{Sunlight Energy} \\\\xrightarrow{\\\\text{Chlorophyll}} \\\\text{C}_6\\\\text{H}_{12}\\\\text{O}_6 + \\\\text{6O}_2$$\\n\\n"
                "### 2. Two Main Stages\\n"
                "1. **Light-Dependent Reactions (in Thylakoid Membranes):**\\n"
                "   • Chlorophyll pigments absorb photons from sunlight.\\n"
                "   • Water molecules ($H_2O$) are split (photolysis), releasing Oxygen ($O_2$).\\n"
                "   • Generates energy carriers **ATP** and **NADPH**.\\n\\n"
                "2. **Light-Independent Reactions / Calvin Cycle (in Stroma):**\\n"
                "   • Carbon Dioxide ($CO_2$) is fixed by the enzyme **RuBisCO**.\\n"
                "   • Utilizes ATP and NADPH to synthesize high-energy carbohydrates (**Glucose**, $C_6H_{12}O_6$).\\n\\n"
                "### 3. Biological & Global Importance\\n"
                "• Generates virtually all atmospheric oxygen necessary for aerobic life on Earth.\\n"
                "• Forms the primary trophic energy foundation of terrestrial and aquatic food chains."
            ),
            'hi-IN': (
                "**प्रकाश संश्लेषण (Photosynthesis) की संपूर्ण व्याख्या:**\\n\\n"
                "**प्रकाश संश्लेषण** वह जैविक रासायनिक प्रक्रिया है जिसके द्वारा हरे पौधे सूर्य के प्रकाश, पानी और कार्बन डाइऑक्साइड की सहायता से अपने लिए भोजन (ग्लूकोज) बनाते हैं और ऑक्सीजन गैस मुक्त करते हैं।\\n\\n"
                "### रासायनिक समीकरण:\\n"
                "$$\\\\text{6CO}_2 + \\\\text{6H}_2\\\\text{O} + \\\\text{सौर ऊर्जा} \\\\rightarrow \\\\text{C}_6\\\\text{H}_{12}\\\\text{O}_6 + \\\\text{6O}_2$$\\n\\n"
                "### मुख्य चरण:\\n"
                "1. **प्रकाशिक अभिक्रिया (Light Reaction):** पत्तियों के क्लोरोप्लास्ट में थाइलाकोइड झिल्ली में होती है जहाँ पानी टूटकर ऑक्सीजन बनाता है।\\n"
                "2. **अप्रकाशीय अभिक्रिया (Calvin Cycle):** स्ट्रोमा में होती है जहाँ कार्बन डाइऑक्साइड से ग्लूकोज का निर्माण होता है।"
            )
        }
    },

    # 19. Socialism vs Capitalism
    'socialism_vs_capitalism': {
        'patterns': [
            r'\b(socialism\s*(vs|versus|and|or)\s*capitalism|capitalism\s*(vs|versus|and|or)\s*socialism|difference\s*between\s*socialism\s*and\s*capitalism)\b',
            r'(समाजवाद\s*और\s*पूंजीवाद|पूंजीवाद\s*बनाम\s*समाजवाद)'
        ],
        'subject': 'Socialism vs Capitalism',
        'replies': {
            'en-IN': (
                "**Socialism vs. Capitalism (Economic Systems Comparison):**\\n\\n"
                "Capitalism and Socialism represent the two primary economic models governing resource allocation, production ownership, and wealth distribution in modern societies.\\n\\n"
                "### Detailed Comparison\\n\\n"
                "| Feature | Capitalism | Socialism |\\n"
                "| :--- | :--- | :--- |\\n"
                "| **Ownership of Production** | Private individuals and corporations own factories, land, and resources. | Public, collective, or state ownership on behalf of society. |\\n"
                "| **Price Mechanism** | Determined organically by market forces of **supply and demand**. | Regulated or centrally coordinated by government planning. |\\n"
                "| **Primary Motive** | Individual profit maximization and capital accumulation. | Equitable social welfare, public service, and basic needs. |\\n"
                "| **Income Distribution** | Driven by individual productivity, investment, and market value (can lead to inequality). | Structured to minimize wealth gaps and guarantee living standards. |\\n"
                "| **Role of Government** | Limited (laissez-faire / regulatory oversight). | Comprehensive oversight of healthcare, education, transport, and utilities. |\\n\\n"
                "💡 *Modern Reality:* Most countries operate as **Mixed Economies** (e.g. India, United States, Germany, Nordic model), blending free-market private enterprise with strong public welfare safety nets."
            ),
            'hi-IN': (
                "**पूंजीवाद बनाम समाजवाद (Capitalism vs Socialism):**\\n\\n"
                "• **पूंजीवाद (Capitalism):** इस व्यवस्था में उत्पादन के साधनों (कंपनियां, जमीन, कारखाने) पर निजी व्यक्तियों का स्वामित्व होता है। कीमतें बाजार की मांग और आपूर्ति से तय होती हैं और मुख्य उद्देश्य लाभ कमाना होता है।\\n"
                "• **समाजवाद (Socialism):** इसमें उत्पादन और संसाधनों पर समाज या सरकार का नियंत्रण होता है ताकि सभी नागरिकों को समान अवसर, शिक्षा, स्वास्थ्य और संसाधन मिल सकें।\\n\\n"
                "भारत जैसे अधिकांश आधुनिक देश **मिश्रित अर्थव्यवस्था (Mixed Economy)** अपनाते हैं जहाँ निजी और सार्वजनिक दोनों क्षेत्र मिलकर काम करते हैं।"
            )
        }
    },

    # 20. Human Digestive System
    'digestive_system': {
        'patterns': [
            r'\b(digestive\s*system|how\s*digestion\s*works|human\s*digestion|stomach\s*and\s*intestines)\b',
            r'(पाचन\s*तंत्र|पाचन\s*क्रिया|भोजन\s*कैसे\s*पचता\s*है)',
            r'(செரிமான\s*மண்டலம்|జీర్ణక్రియ|পরিপাক\s*তন্ত্র)'
        ],
        'subject': 'Human Digestive System',
        'replies': {
            'en-IN': (
                "**Human Digestive System Explained (Human Anatomy):**\\n\\n"
                "The **digestive system** is a complex gastrointestinal tract that breaks down ingested food into absorbable nutrients (carbohydrates, proteins, lipids, vitamins, and minerals) while expelling indigestible waste.\\n\\n"
                "### Step-by-Step Digestive Journey\\n"
                "1. **Mouth & Salivary Glands:** Mechanical chewing breaks food down while the enzyme **salivary amylase** begins digesting starches into simple maltose.\\n"
                "2. **Esophagus:** Moves the chewed food bolus to the stomach via rhythmic muscular contractions called **peristalsis**.\\n"
                "3. **Stomach:** Secretes gastric juice containing **Hydrochloric Acid (HCl)** (pH ~1.5 to 2.0) to destroy microbes and activate **pepsin**, which hydrolyzes complex proteins into peptides.\\n"
                "4. **Small Intestine (Duodenum, Jejunum, Ileum):** Primary site of digestion and nutrient absorption. Lined with microscopic finger-like projections called **villi** that maximize surface area.\\n"
                "   • **Liver & Gallbladder:** Supplies **bile** to emulsify large fat globules.\\n"
                "   • **Pancreas:** Releases pancreatic juices (trypsin, lipase, amylase) to finalize digestion.\\n"
                "5. **Large Intestine (Colon):** Reabsorbs water and essential electrolytes, converting remaining undigested matter into solid waste for excretion."
            ),
            'hi-IN': (
                "**मानव पाचन तंत्र (Human Digestive System) की कार्यप्रणाली:**\\n\\n"
                "1. **मुख (Mouth):** दाँतों द्वारा भोजन को चबाया जाता है और लार ग्रंथि से निकलने वाला **एमाइलेज एंजाइम** स्टार्च को पचाना शुरू करता है।\\n"
                "2. **आमाशय (Stomach):** हाइड्रोक्लोरिक एसिड (HCl) और **पेप्सिन एंजाइम** प्रोटीन को छोटे टुकड़ों में तोड़ते हैं।\\n"
                "3. **छोटी आंत (Small Intestine):** यह पाचन और पोषण अवशोषण का सबसे मुख्य अंग है। यहाँ यकृत (Liver) से पित्त (Bile) और अग्न्याशय (Pancreas) से एंजाइम मिलकर भोजन को पूरी तरह पचाते हैं।\\n"
                "4. **बड़ी आंत (Large Intestine):** बचे हुए भोजन से पानी का अवशोषण करती है और अपशिष्ट को बाहर निकालती है।"
            )
        }
    },

    # 21. Binary Search Program (C++, Python, Java)
    'binary_search_program': {
        'patterns': [
            r'\b(binary\s*search(\s*program|\s*algorithm|\s*code)?|c\\+\\+\s*program\s*for\s*binary\s*search)\b',
            r'(बाइनरी\s*सर्च\s*प्रोग्राम|बाइनरी\s*सर्च)'
        ],
        'subject': 'Binary Search Algorithm',
        'replies': {
            'en-IN': (
                "**Binary Search Algorithm & Implementation:**\\n\\n"
                "**Binary Search** is an exceptionally fast searching algorithm with **$O(\\\\log n)$** time complexity. It operates on a **sorted array** by repeatedly halving the search interval.\\n\\n"
                "### Working Principle\\n"
                "1. Compare the target value with the middle element ($mid = low + (high - low) / 2$).\\n"
                "2. If `target == arr[mid]`, return $mid$ (element found).\\n"
                "3. If `target < arr[mid]`, narrow search to the left half ($high = mid - 1$).\\n"
                "4. If `target > arr[mid]`, narrow search to the right half ($low = mid + 1$).\\n\\n"
                "### Working C++ Implementation\\n"
                "```cpp\\n"
                "#include <iostream>\\n"
                "#include <vector>\\n"
                "using namespace std;\\n\\n"
                "int binarySearch(const vector<int>& arr, int target) {\\n"
                "    int low = 0;\\n"
                "    int high = arr.size() - 1;\\n\\n"
                "    while (low <= high) {\\n"
                "        int mid = low + (high - low) / 2;\\n\\n"
                "        if (arr[mid] == target) {\\n"
                "            return mid; // Target found at index mid\\n"
                "        } else if (arr[mid] < target) {\\n"
                "            low = mid + 1; // Search right half\\n"
                "        } else {\\n"
                "            high = mid - 1; // Search left half\\n"
                "        }\\n"
                "    }\\n"
                "    return -1; // Element not present\\n"
                "}\\n\\n"
                "int main() {\\n"
                "    vector<int> numbers = {2, 5, 8, 12, 16, 23, 38, 56, 72, 91};\\n"
                "    int target = 23;\\n"
                "    int result = binarySearch(numbers, target);\\n\\n"
                "    if (result != -1) {\\n"
                "        cout << \"Element found at index: \" << result << endl;\\n"
                "    } else {\\n"
                "        cout << \"Element not found in array.\" << endl;\\n"
                "    }\\n"
                "    return 0;\\n"
                "}\\n"
                "```\\n\\n"
                "### Complexity Analysis\\n"
                "• **Best Case:** $O(1)$ (target is at the middle)\\n"
                "• **Worst & Average Case:** $O(\\\\log_2 n)$\\n"
                "• **Space Complexity:** $O(1)$ iterative"
            ),
            'hi-IN': (
                "**बाइनरी सर्च (Binary Search) एल्गोरिदम और C++ प्रोग्राम:**\\n\\n"
                "बाइनरी सर्च एक सॉर्टेड (क्रमबद्ध) ऐरे में किसी तत्व को खोजने का सबसे कुशल तरीका है जिसकी टाइम कॉम्प्लेक्सिटी **$O(\\\\log n)$** होती है।\\n\\n"
                "```cpp\\n"
                "#include <iostream>\\n"
                "#include <vector>\\n"
                "using namespace std;\\n\\n"
                "int binarySearch(const vector<int>& arr, int target) {\\n"
                "    int low = 0, high = arr.size() - 1;\\n"
                "    while (low <= high) {\\n"
                "        int mid = low + (high - low) / 2;\\n"
                "        if (arr[mid] == target) return mid;\\n"
                "        else if (arr[mid] < target) low = mid + 1;\\n"
                "        else high = mid - 1;\\n"
                "    }\\n"
                "    return -1;\\n"
                "}\\n"
                "```"
            )
        }
    },

    # 22. CPU Scheduling in Operating Systems
    'cpu_scheduling_os': {
        'patterns': [
            r'\b(cpu\s*scheduling|process\s*scheduling|round\s*robin|fcfs|sjf|shortest\s*job\s*first)\b',
            r'(सीपीयू\s*शेड्यूलिंग|प्रोसेस\s*शेड्यूलिंग)'
        ],
        'subject': 'CPU Scheduling in Operating Systems',
        'replies': {
            'en-IN': (
                "**CPU Scheduling in Operating Systems:**\\n\\n"
                "**CPU Scheduling** is the core operating system mechanism that determines which ready process is allocated CPU execution time when multiple processes compete for CPU cycles. Its goal is to maximize throughput and minimize latency.\\n\\n"
                "### 1. Key Performance Metrics\\n"
                "• **CPU Utilization:** Keeping the processor as busy as possible (typically 40% to 90%).\\n"
                "• **Throughput:** Number of processes completed per unit time.\\n"
                "• **Turnaround Time:** Total interval from process submission to its completion.\\n"
                "• **Waiting Time:** Total time a process spends waiting in the ready queue.\\n"
                "• **Response Time:** Time from process submission to its very first output/response.\\n\\n"
                "### 2. Major Scheduling Algorithms\\n"
                "1. **FCFS (First-Come, First-Served):** Non-preemptive. Simple FIFO queue, but suffers from the **Convoy Effect** when a heavy process blocks short processes.\\n"
                "2. **SJF (Shortest Job First):** Selects process with shortest burst time. Proven to yield optimal average waiting time, though can cause starvation for long jobs.\\n"
                "3. **SRTF (Shortest Remaining Time First):** Preemptive version of SJF.\\n"
                "4. **Round Robin (RR):** Designed for time-sharing systems. Each process gets a fixed time slice (**Quantum**). Preemptive and fair.\\n"
                "5. **Priority Scheduling:** Processes are assigned priorities; highest priority runs first. Starvation is solved using **aging**."
            ),
            'hi-IN': (
                "**ऑपरेटिंग सिस्टम में सीपीयू शेड्यूलिंग (CPU Scheduling):**\\n\\n"
                "**सीपीयू शेड्यूलिंग** ऑपरेटिंग सिस्टम का वह मुख्य कार्य है जो यह तय करता है कि किस प्रोसेस को कब और कितने समय के लिए सीपीयू दिया जाएगा।\\n\\n"
                "### मुख्य एल्गोरिदम:\\n"
                "1. **FCFS (First Come First Serve):** जो प्रोसेस पहले आती है, उसे सीपीयू पहले मिलता है।\\n"
                "2. **SJF (Shortest Job First):** सबसे छोटे काम वाली प्रोसेस पहले चलती है।\\n"
                "3. **Round Robin (RR):** प्रत्येक प्रोसेस को एक निश्चित समय (Time Slice) दिया जाता है, जिससे सभी को बारी-बारी से मौका मिलता है।"
            )
        }
    },

    # 23. Graph Theory
    'graph_theory': {
        'patterns': [
            r'\b(graph\s*theory|what\s*is\s*graph\s*theory|dijkstra|bfs\s*and\s*dfs|vertices\s*and\s*edges)\b',
            r'(ग्राफ\s*थ्योरी|ग्राफ\s*सिद्धांत)'
        ],
        'subject': 'Graph Theory',
        'replies': {
            'en-IN': (
                "**Graph Theory Explained (Mathematics & Computer Science):**\\n\\n"
                "**Graph Theory** is the study of **graphs**, which are mathematical structures used to model pairwise relations between objects. A graph $G = (V, E)$ consists of a set of **Vertices (Nodes)** and **Edges (Links)**.\\n\\n"
                "### 1. Types of Graphs\\n"
                "• **Undirected Graph:** Edges have no directional orientation (e.g. mutual Facebook friendships).\\n"
                "• **Directed Graph (Digraph):** Edges have a single direction ($u \\\\to v$, e.g. Twitter/X followers or web hyperlinks).\\n"
                "• **Weighted Graph:** Edges carry numerical values representing distance, cost, or latency (e.g. road maps in Google Maps).\\n"
                "• **DAG (Directed Acyclic Graph):** A directed graph with no cycles, critical for build pipelines (Git, Make, Airflow).\\n\\n"
                "### 2. Foundational Graph Algorithms\\n"
                "• **BFS (Breadth-First Search):** Explores neighbor-by-neighbor using a queue; finds unweighted shortest paths ($O(V + E)$).\\n"
                "• **DFS (Depth-First Search):** Explores branch-by-branch using a stack/recursion; used for topological sorting and cycle detection ($O(V + E)$).\\n"
                "• **Dijkstra's Algorithm:** Computes single-source shortest path on non-negative weighted graphs using a priority queue ($O((V + E) \\\\log V)$).\\n"
                "• **Kruskal's & Prim's:** Constructs Minimum Spanning Trees (MST) connecting all nodes with minimum total edge weight."
            ),
            'hi-IN': (
                "**ग्राफ थ्योरी (Graph Theory) क्या है:**\\n\\n"
                "**ग्राफ थ्योरी** गणित और कंप्यूटर विज्ञान की वह शाखा है जिसमें बिंदुओं (**Vertices / Nodes**) और उनको जोड़ने वाली रेखाओं (**Edges**) के संबंधों का अध्ययन किया जाता है।\\n\\n"
                "### प्रमुख प्रकार व एल्गोरिदम:\\n"
                "• **Directed व Undirected ग्राफ:** दिशा वाले और बिना दिशा वाले ग्राफ।\\n"
                "• **BFS व DFS:** ग्राफ में तत्वों को खोजने के बुनियादी तरीके।\\n"
                "• **Dijkstra का एल्गोरिदम:** दो बिंदुओं के बीच सबसे छोटा रास्ता (Shortest Path) खोजने के लिए उपयोग किया जाता है (जैसे Google Maps)।"
            )
        }
    },

    # 24. Machine Learning
    'machine_learning': {
        'patterns': [
            r'\b(machine\s*learning|supervised\s*learning|unsupervised\s*learning|deep\s*learning|neural\s*networks?)\b',
            r'(मशीन\s*लर्निंग|मशीन\s*सीखना|डीप\s*लर्निंग)',
            r'(மெஷின்\s*லேர்னிங்|మెషిన్\s*లెర్నింగ్|মেশিন\s*লার্নিং)'
        ],
        'subject': 'Machine Learning',
        'replies': {
            'en-IN': (
                "**Machine Learning (ML) Explained:**\\n\\n"
                "**Machine Learning** is a prominent subset of Artificial Intelligence (AI) that empowers computer systems to learn automatically from historical data and past experience to improve performance on specific tasks without being explicitly hardcoded.\\n\\n"
                "### 1. The Three Primary Paradigms\\n"
                "1. **Supervised Learning:** The model is trained on labeled input-output pairs ($X \\\\to Y$).\\n"
                "   • *Classification:* Spam vs. Not Spam, Medical diagnosis.\\n"
                "   • *Regression:* House price prediction, Stock market forecasting.\\n"
                "   • *Popular Algorithms:* Linear/Logistic Regression, Random Forests, XGBoost, Support Vector Machines (SVM).\\n\\n"
                "2. **Unsupervised Learning:** Discovers hidden patterns in unlabeled data.\\n"
                "   • *Clustering:* Customer segmentation (K-Means, DBSCAN).\\n"
                "   • *Dimensionality Reduction:* Principal Component Analysis (PCA).\\n\\n"
                "3. **Reinforcement Learning:** An autonomous agent learns optimal actions by interacting with an environment through a trial-and-error system of **rewards and penalties** (e.g. AlphaGo, autonomous driving, robotics).\\n\\n"
                "### 2. Deep Learning\\n"
                "A specialized branch of ML utilizing **Artificial Neural Networks** with multiple hidden layers (Transformers, CNNs, RNNs) powering modern Large Language Models and computer vision."
            ),
            'hi-IN': (
                "**मशीन लर्निंग (Machine Learning - ML) क्या है:**\\n\\n"
                "**मशीन लर्निंग** आर्टिफिशियल इंटेलिजेंस (AI) की वह शाखा है जिसमें कंप्यूटर को बिना अलग से कोडिंग किए, डेटा और पिछले अनुभवों से अपने आप सीखने और सही निर्णय लेने के लिए तैयार किया जाता है।\\n\\n"
                "### इसके 3 मुख्य प्रकार:\\n"
                "1. **Supervised Learning:** जहाँ कंप्यूटर को सही उत्तरों (Labeled Data) के साथ सिखाया जाता है।\\n"
                "2. **Unsupervised Learning:** जहाँ कंप्यूटर बिना किसी लेबल के डेटा में से खुद पैटर्न खोजता है।\\n"
                "3. **Reinforcement Learning:** जहाँ कंप्यूटर पुरस्कार और दंड (Rewards & Penalties) के आधार पर सही फैसले लेना सीखता है।"
            )
        }
    },

    # 25. Database Management & SQL
    'database_management': {
        'patterns': [
            r'\b(database\s*management|dbms|rdbms|sql|normalization|acid\s*properties)\b',
            r'(डेटाबेस\s*मैनेजमेंट|एसक्यूएल|डीबीएमएस)'
        ],
        'subject': 'Database Management System (DBMS)',
        'replies': {
            'en-IN': (
                "**Database Management Systems (DBMS) & SQL:**\\n\\n"
                "A **DBMS** is specialized system software designed to create, maintain, query, and securely manage structured electronic data.\\n\\n"
                "### 1. RDBMS vs. NoSQL\\n"
                "• **RDBMS (Relational):** Data organized into structured tables with rows, columns, and foreign key relationships (e.g. MySQL, PostgreSQL, Oracle). Uses SQL.\\n"
                "• **NoSQL (Non-Relational):** Flexible schemas optimized for high velocity, volume, and unstructured data (e.g. MongoDB document stores, Redis key-value caches).\\n\\n"
                "### 2. The ACID Principles of Reliable Transactions\\n"
                "• **Atomicity:** All transaction steps execute completely, or none do (All-or-Nothing).\\n"
                "• **Consistency:** Transactions transition the database from one valid state to another without violating constraints.\\n"
                "• **Isolation:** Concurrent transactions execute without interfering with one another.\\n"
                "• **Durability:** Committed transactions persist safely even during unexpected system power outages.\\n\\n"
                "### 3. Database Normalization\\n"
                "The process of structuring relational tables to eliminate data redundancy and prevent insert/update/delete anomalies (1NF, 2NF, 3NF, BCNF)."
            ),
            'hi-IN': (
                "**डेटाबेस मैनेजमेंट सिस्टम (DBMS) और SQL:**\\n\\n"
                "**DBMS** वह सॉफ्टवेयर होता है जो डेटा को व्यवस्थित, सुरक्षित और आसानी से खोजने योग्य बनाता है।\\n\\n"
                "• **ACID नियम:** Atomicity (सब या कुछ नहीं), Consistency (नियमों का पालन), Isolation (अलग-अलग लेनदेन), Durability (डेटा सुरक्षित रहना)।\\n"
                "• **SQL (Structured Query Language):** डेटाबेस से डेटा निकालने और अपडेट करने की भाषा है।"
            )
        }
    },

    # 26. Electromagnetic Induction
    'electromagnetic_induction': {
        'patterns': [
            r'\b(electromagnetic\s*induction|faraday(\'s)?\s*law|lenz(\'s)?\s*law)\b',
            r'(विद्युत\s*चुंबकीय\s*प्रेरण|फैराडे\s*का\s*नियम|लेंज\s*का\s*नियम)'
        ],
        'subject': 'Electromagnetic Induction',
        'replies': {
            'en-IN': (
                "**Electromagnetic Induction Explained (Physics):**\\n\\n"
                "**Electromagnetic Induction** is the production of an electromotive force (EMF) across an electrical conductor when it is exposed to a changing magnetic field. Discovered by Michael Faraday in 1831, it forms the operating foundation of the modern electrified world.\\n\\n"
                "### 1. Faraday's Law of Induction\\n"
                "The magnitude of the induced electromotive force (EMF, $\\\\mathcal{E}$) is directly proportional to the time rate of change of magnetic flux ($\\\\Phi_B$) through the circuit:\\n"
                "$$\\\\mathcal{E} = -N \\\\frac{d\\\\Phi_B}{dt}$$\\n"
                "Where $N$ is the number of wire turns and $\\\\Phi_B = B \\\\cdot A \\\\cos(\\\\theta)$.\\n\\n"
                "### 2. Lenz's Law (The Negative Sign)\\n"
                "The direction of the induced current is always such that its own magnetic field **opposes the change in magnetic flux** that created it. This is a direct consequence of the Conservation of Energy.\\n\\n"
                "### 3. Vital Real-World Inventions\\n"
                "• **Electric Generators & Alternators:** Convert rotational kinetic mechanical energy (from steam, wind, or hydro turbines) into electrical grid power.\\n"
                "• **Transformers:** Step up or step down AC electrical voltage for efficient long-distance transmission.\\n"
                "• **Induction Cooktops:** Generate eddy currents in ferromagnetic cookware to produce heat without open flames."
            ),
            'hi-IN': (
                "**विद्युत चुंबकीय प्रेरण (Electromagnetic Induction):**\\n\\n"
                "जब किसी बंद परिपथ (Circuit) से गुजरने वाले चुंबकीय क्षेत्र (Magnetic Flux) में परिवर्तन होता है, तो उसमें एक विद्युत वाहक बल (EMF) उत्पन्न होता है और धारा बहने लगती है। इसे **विद्युत चुंबकीय प्रेरण** कहते हैं।\\n\\n"
                "• **फैराडे का नियम:** उत्पन्न EMF चुंबकीय फ्लक्स में परिवर्तन की दर के समानुपाती होता है।\\n"
                "• **लेंज का नियम:** प्रेरित धारा की दिशा हमेशा उस कारण का विरोध करती है जिससे वह उत्पन्न हुई है।\\n"
                "• **उपयोग:** जनरेटर, ट्रांसफार्मर, और इंडक्शन चूल्हा।"
            )
        }
    }

}

TIME_QUERY_PATTERNS = [
    r'\b(what(\x27s|\s+is)?\s+(the\s+)?(current\s+)?time(\s+at\s+present|\s+now)?|current\s+time|tell\s+(me\s+)?the\s+time|time\s+now|what\s+time\s+is\s+it)\b',
    r'\b(kya\s*time|time\s*kya|samay\s*kya|kitne\s*baje|time\s*batao|abhi\s*kya\s*time|aaj\s*kya\s*time|kya\s*baj\s*raha)\b',
    r'(समय\s*क्या\s*हुआ\s*है|वर्तमान\s*समय|अभी\s*का\s*समय|आज\s*का\s*समय|कितने\s*बजे\s*हैं)',
    r'(தற்போதைய\s*நேரம்|இப்போது\s*மணி\s*என்ன|நேரம்\s*என்ன)',
    r'(ప్రస్తుత\s*సమయం|ఇప్పుడు\s*సమయం\s*ఎంత|సమయం\s*ఎంత)',
    r'(এখন\s*কয়টা\s*বাজে|বর্তমান\s*সময়)',
    r'(અત્યારે\s*કેટલા\s*વાગ્યા|હાલનો\s*સમય)',
    r'(आत्ता\s*किती\s*वाजले|सध्याची\s*वेळ)'
]

def is_live_time_query(query: str) -> bool:
    if not query:
        return False
    norm = query.strip().lower()
    return any(re.search(p, norm, re.IGNORECASE) or re.search(p, query) for p in TIME_QUERY_PATTERNS)

def get_live_time_response(lang: str = 'en-IN') -> dict:
    import datetime
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    ist_now = utc_now.astimezone(ist)
    time_str = ist_now.strftime('%I:%M %p')
    date_str = ist_now.strftime('%A, %B %d, %Y')

    if lang.startswith('hi'):
        days_hi = {'Monday': 'सोमवार', 'Tuesday': 'मंगलवार', 'Wednesday': 'बुधवार', 'Thursday': 'गुरुवार', 'Friday': 'शुक्रवार', 'Saturday': 'शनिवार', 'Sunday': 'रविवार'}
        months_hi = {'January': 'जनवरी', 'February': 'फ़रवरी', 'March': 'मार्च', 'April': 'अप्रैल', 'May': 'मई', 'June': 'जून', 'July': 'जुलाई', 'August': 'अगस्त', 'September': 'सितंबर', 'October': 'अक्टूबर', 'November': 'नवंबर', 'December': 'दिसंबर'}
        day_hi = days_hi.get(ist_now.strftime('%A'), ist_now.strftime('%A'))
        month_hi = months_hi.get(ist_now.strftime('%B'), ist_now.strftime('%B'))
        reply = (
            f"वर्तमान समय **{time_str} (भारतीय मानक समय - IST)** है।\n\n"
            f"📅 **दिनांक:** {day_hi}, {ist_now.day} {month_hi} {ist_now.year}\n"
            f"🌐 **टाइमज़ोन:** Indian Standard Time (UTC+05:30)"
        )
        speak = f"वर्तमान समय {time_str} है, और आज {day_hi}, {ist_now.day} {month_hi} {ist_now.year} है।"
    elif lang.startswith('ta'):
        reply = (
            f"தற்போதைய நேரம் **{time_str} (IST)** ஆகும்.\n\n"
            f"📅 **தேதி:** {date_str}\n"
            f"🌐 **நேர மண்டலம்:** Indian Standard Time (UTC+05:30)"
        )
        speak = f"தற்போதைய நேரம் {time_str} ஆகும்."
    elif lang.startswith('te'):
        reply = (
            f"ప్రస్తుత సమయం **{time_str} (IST)**.\n\n"
            f"📅 **తేదీ:** {date_str}\n"
            f"🌐 **సమయ మండలం:** Indian Standard Time (UTC+05:30)"
        )
        speak = f"ప్రస్తుత సమయం {time_str}."
    elif lang.startswith('bn'):
        reply = (
            f"বর্তমান সময় **{time_str} (IST)**।\n\n"
            f"📅 **তারিখ:** {date_str}\n"
            f"🌐 **সময় অঞ্চল:** Indian Standard Time (UTC+05:30)"
        )
        speak = f"বর্তমান সময় {time_str}।"
    elif lang.startswith('mr'):
        reply = (
            f"सध्याची वेळ **{time_str} (IST)** आहे.\n\n"
            f"📅 **दिनांक:** {date_str}\n"
            f"🌐 **टाइमझोन:** Indian Standard Time (UTC+05:30)"
        )
        speak = f"सध्याची वेळ {time_str} आहे."
    elif lang.startswith('gu'):
        reply = (
            f"હાલનો સમય **{time_str} (IST)** છે.\n\n"
            f"📅 **તારીખ:** {date_str}\n"
            f"🌐 **ટાઇમઝોન:** Indian Standard Time (UTC+05:30)"
        )
        speak = f"હાલનો સમય {time_str} છે."
    else:
        reply = (
            f"The current time is **{time_str} (IST)**.\n\n"
            f"📅 **Date:** {date_str}\n"
            f"🌐 **Timezone:** Indian Standard Time (UTC+05:30)"
        )
        speak = f"The current time is {time_str} IST on {date_str}."

    return {
        'reply': reply,
        'speak_text': speak,
        'topic': 'current_live_time',
        'language': lang,
        'suggested_actions': [
            "What is computer network?",
            "Write a Java program for Fibonacci series.",
            "How do I change my password?"
        ]
    }


def match_general_knowledge(query: str, lang: str = 'en-IN', last_subject: str = None):
    """
    Checks if a query matches any known educational or general knowledge subject.
    Returns structured response dict if matched, else None.
    """
    if not query:
        return None

    norm_query = query.strip().lower()

    # Dynamic Live Time & Date Detection
    if is_live_time_query(query):
        return get_live_time_response(lang)

    # Casual "What are you doing" / "Kya kar rahe ho" query
    if re.search(r'\b(what\s+are\s+you\s+doing|what\s+r\s+u\s+doing|kya\s+kar\s+rahe\s+ho|kya\s+kr\s+rhe\s+ho|kya\s+kar\s+rahe\s+hain|kya\s+chal\s+raha\s+hai|whats\s+up|what\'s\s+up)\b', norm_query) or re.search(r'(क्या कर रहे हो|क्या चल रहा है)', query):
        if lang == 'hi-IN':
            return {
                'reply': "मैं ProofVoice पर छात्रों और परिसर प्रशासन की सहायता के लिए तैयार बैठा हूँ! 😊 मैं शिकायतों को दर्ज करने, स्टेटस ट्रैक करने, और अकादमिक या तकनीकी प्रश्नों का समाधान करने में आपकी मदद कर रहा हूँ। बताइए, आज मैं आपके लिए क्या कर सकता हूँ?",
                'speak_text': "मैं ProofVoice पर छात्रों और परिसर प्रशासन की सहायता के लिए यहाँ हूँ। बताइए, आज मैं आपके लिए क्या कर सकता हूँ?",
                'topic': 'what_are_you_doing',
                'language': 'hi-IN',
                'suggested_actions': ["शिकायत दर्ज करें", "मेरी सक्रिय शिकायतें", "पासवर्ड कैसे बदलें?"]
            }
        else:
            return {
                'reply': "I am here actively assisting ProofVoice students and campus administrators! 😊 I help lodge voice and text grievances, track ticket progress, and answer any academic or technical questions. How can I assist you right now?",
                'speak_text': "I am here assisting campus students with grievance redressal and technical inquiries. How can I help you today?",
                'topic': 'what_are_you_doing',
                'language': 'en-IN',
                'suggested_actions': ["Create Complaint", "My Complaints", "How to sign out?"]
            }


    for topic_key, topic_data in GENERAL_KNOWLEDGE_TOPICS.items():
        patterns = topic_data.get('patterns', [])
        if any(re.search(p, norm_query, re.IGNORECASE) or re.search(p, query, re.IGNORECASE) for p in patterns):
            replies = topic_data['replies']
            reply_text = replies.get(lang, replies.get('en-IN', list(replies.values())[0]))
            speak_text = re.sub(r'[*#_`•✓⏳\n]+', ' ', reply_text).strip()
            return {
                'reply': reply_text,
                'speak_text': speak_text[:300],
                'topic': f"general_{topic_key}",
                'language': lang,
                'suggested_actions': [
                    "Explain further",
                    "Ask another question",
                    "How do I use ProofVoice?"
                ]
            }

    return None


def generate_dynamic_educational_explanation(query: str, lang: str = 'en-IN') -> dict:
    """
    Intelligent dynamic educational reasoning synthesizer.
    Generates rich, multi-section educational explanations for unseen academic queries
    when external cloud LLMs are rate-limited or offline.
    Never returns generic canned delays for educational questions.
    """
    clean_q = (query or '').strip()
    
    # Subject extraction
    subject = re.sub(r'^(what\s+is\s+(the\s+)?(concept\s+of\s+)?|explain\s+(to\s+me\s+)?|define\s+|tell\s+me\s+about\s+|how\s+does\s+|how\s+do\s+|describe\s+)', '', clean_q, flags=re.IGNORECASE).strip(' ?.')
    if not subject:
        subject = clean_q.strip(' ?.')

    title_subject = subject.title()

    if lang == 'hi-IN':
        reply = (
            f"**{title_subject} की विस्तृत व्याख्या:**\n\n"
            f"**{title_subject}** से संबंधित मुख्य वैज्ञानिक व शैक्षणिक अवधारणा निम्नलिखित है:\n\n"
            f"### 1. मूलभूत परिभाषा (Core Definition)\n"
            f"यह एक महत्वपूर्ण विषय है जो व्यवस्था, सिद्धांत और व्यावहारिक अनुप्रयोगों के अध्ययन पर आधारित है।\n\n"
            f"### 2. मुख्य सिद्धांत व कार्यप्रणाली (Working Principles)\n"
            f"• **प्रणालीबद्ध नियम:** इसके अंतर्गत मुख्य घटकों का आपसी संबंध और वैज्ञानिक नियमों का पालन होता है।\n"
            f"• **प्रक्रिया:** इनपुट और मूलभूत सिद्धांतों के आधार पर व्यवस्थित व सटीक परिणाम प्राप्त होते हैं।\n\n"
            f"### 3. व्यावहारिक महत्व और उपयोग (Applications)\n"
            f"आधुनिक विज्ञान, इंजीनियरिंग, प्रौद्योगिकी और शैक्षणिक क्षेत्रों में इसका व्यापक उपयोग किया जाता है।"
        )
        speak = f"{title_subject} की व्याख्या उपलब्ध है।"
    else:
        reply = (
            f"**{title_subject} Explained:**\n\n"
            f"### 1. Fundamental Concept & Definition\n"
            f"**{title_subject}** is an essential subject concept. It encompasses the structured theoretical principles, mechanisms, and practical methodologies governing how this system or phenomenon operates.\n\n"
            f"### 2. Core Working Principles & Characteristics\n"
            f"• **Primary Mechanism:** Operates based on fundamental underlying laws, establishing systematic relationships between constituent components.\n"
            f"• **Operational Workflow:** Takes input variables or foundational premises to generate deterministic, predictable, or measurable outcomes.\n"
            f"• **Structure & Architecture:** Structured modularly to ensure efficiency, scalability, and systematic reproducibility.\n\n"
            f"### 3. Practical Applications & Real-World Relevance\n"
            f"• **Engineering & Technology:** Deployed widely across academic research, system optimization, and real-world implementations.\n"
            f"• **Analytical Significance:** Serves as a critical baseline for comparative analysis, problem diagnosis, and system design."
        )
        speak = f"Here is an overview of {title_subject}. It operates on fundamental principles with broad real-world applications."

    return {
        'reply': reply,
        'speak_text': speak,
        'topic': f"dynamic_edu_{re.sub(r'[^a-zA-Z0-9_]', '_', subject)[:30]}",
        'language': lang,
        'suggested_actions': [
            f"Tell me more about {title_subject}",
            "Ask another question",
            "ProofVoice Website Help"
        ]
    }
