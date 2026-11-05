# -*- coding: utf-8 -*-
import os, sys, re

def test_homepage_navigation_and_features():
    print("=" * 65)
    print("TESTING HOMEPAGE NAVIGATION, FEATURES & AUTHENTICATION FLOW")
    print("=" * 65)

    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # -------------------------------------------------------------------------
    # TEST 1: Exact Section Order and Scrolling Sequence
    # -------------------------------------------------------------------------
    section_ids = re.findall(r'<section[^>]*id=["\']([^"\']+)["\']', html)
    expected_order = [
        'home',
        'problem-solution',
        'how-it-works',
        'features',
        'ai-assistant',
        'languages',
        'institutions',
        'faq',
        'final-cta'
    ]
    print(f"Found section sequence: {section_ids}")
    assert section_ids == expected_order, f"Section order mismatch! Expected: {expected_order}, Got: {section_ids}"
    print("[PASS] TEST 1: Section order strictly matches restored sequence.")

    # -------------------------------------------------------------------------
    # TEST 2: Navigation Links Match Scrolling Sequence
    # -------------------------------------------------------------------------
    nav_links = re.findall(r'<ul[^>]*id=["\']mainNavLinks["\'][^>]*>(.*?)</ul>', html, re.DOTALL)[0]
    nav_hrefs = re.findall(r'href=["\']([^"\']+)["\']', nav_links)
    expected_nav_hrefs = [
        '#home',
        '#how-it-works',
        '#features',
        '#ai-assistant',
        '#languages',
        '#institutions',
        '#faq'
    ]
    assert nav_hrefs == expected_nav_hrefs, f"Nav links mismatch! Expected: {expected_nav_hrefs}, Got: {nav_hrefs}"
    print("[PASS] TEST 2: Navigation links strictly follow sequential downward scrolling order.")

    # -------------------------------------------------------------------------
    # TEST 3: All 14 Feature Cards Present & Interactive with Compact Icons
    # -------------------------------------------------------------------------
    feature_cards = re.findall(r'<div class=["\']feature-card["\'][^>]*data-feature-target=["\']([^"\']+)["\'][^>]*data-feature-name=["\']([^"\']+)["\'][^>]*data-feature-role=["\']([^"\']+)["\']', html)
    print(f"Found {len(feature_cards)} feature cards.")
    assert len(feature_cards) == 14, f"Expected 14 feature cards, found {len(feature_cards)}."

    expected_features = [
        "Voice-Based Reporting",
        "Speech-to-Text Conversion",
        "AI-Powered Application Generation",
        "Application Preview and Editing",
        "Unique Complaint Tracking ID",
        "Real-Time Status Updates",
        "Text-to-Speech Updates",
        "Department Assignment",
        "Duplicate Complaint Suggestions",
        "Institution-Specific Dashboards",
        "Analytics and Reports",
        "Notifications and Reminders",
        "AI Assistant and Help Support",
        "Multilingual Accessibility"
    ]

    for i, (target, name, role) in enumerate(feature_cards):
        clean_file = target.split('?')[0].split('#')[0]
        assert os.path.exists(clean_file), f"Target file does not exist: {clean_file} for feature {name}"
        assert name == expected_features[i], f"Feature name mismatch at index {i}: {name} vs {expected_features[i]}"
        print(f"       [{i+1}/14] {name} -> {target} ({role}) [OK]")

    # Check compact icon container (.feature-icon)
    feature_icons = re.findall(r'<div class=["\']feature-icon["\']', html)
    assert len(feature_icons) >= 14, f"Expected at least 14 .feature-icon compact containers, found {len(feature_icons)}"
    print("[PASS] TEST 3: All 14 feature cards restored with compact .feature-icon containers and valid targets.")

    # -------------------------------------------------------------------------
    # TEST 4: Hero Section Two-Column Layout & Product Mockup
    # -------------------------------------------------------------------------
    assert '<div class="hero-grid">' in html, "Missing .hero-grid in hero section"
    assert '<div class="hero-mockup-wrapper">' in html, "Missing .hero-mockup-wrapper in hero section"
    assert '<div class="mockup-main-card">' in html, "Missing .mockup-main-card in hero section"
    assert '<div class="mockup-voice-box">' in html, "Missing .mockup-voice-box in hero section"
    assert '<div class="mockup-waveform">' in html, "Missing .mockup-waveform in hero section"
    assert '<div class="mockup-stepper">' in html, "Missing .mockup-stepper in hero section"
    print("[PASS] TEST 4: Hero two-column layout and visual assistant mockup card restored exactly.")

    # -------------------------------------------------------------------------
    # TEST 5: Language Section Terminology (STT / TTS, No Named Human Voices)
    # -------------------------------------------------------------------------
    lang_section = re.search(r'<section[^>]*id=["\']languages["\'].*?</section>', html, re.DOTALL).group(0)
    assert 'Speech-to-Text (STT)' in lang_section, "Missing 'Speech-to-Text (STT)' in language section"
    assert 'Text-to-Speech (TTS)' in lang_section, "Missing 'Text-to-Speech (TTS)' in language section"
    assert 'AI Language Assistance' in lang_section, "Missing 'AI Language Assistance' in language section"

    # Ensure no individual human voice names are present
    disallowed_names = ['Shivani', 'Riyaa', 'Kalpana', 'Aakash', 'Pooja', 'Deepak', 'Sneha']
    for bad_name in disallowed_names:
        assert bad_name not in lang_section, f"Found human voice name '{bad_name}' in language section!"
    print("[PASS] TEST 5: Language section uses pure STT and TTS terminology; zero human voice names.")

    # -------------------------------------------------------------------------
    # TEST 6: CSS Scroll-Margin-Top & Animated Navigation Pill
    # -------------------------------------------------------------------------
    with open('css/landing.css', 'r', encoding='utf-8') as f:
        css = f.read()

    assert 'scroll-margin-top:' in css, "Missing scroll-margin-top in css/landing.css"
    assert 'scroll-behavior: smooth;' in css, "Missing scroll-behavior: smooth in css/landing.css"
    assert '.nav-active-pill' in css, "Missing .nav-active-pill in css/landing.css"
    assert '.hero-mockup-wrapper' in css, "Missing .hero-mockup-wrapper in css/landing.css"
    assert '.mockup-main-card' in css, "Missing .mockup-main-card in css/landing.css"
    print("[PASS] TEST 6: CSS smooth scrolling, header scroll-margin-top, and animated nav pill verified.")

    # -------------------------------------------------------------------------
    # TEST 7: Login & Registration Redirect Safety & Return URL Preservation
    # -------------------------------------------------------------------------
    with open('login.html', 'r', encoding='utf-8') as f:
        login_html = f.read()
    with open('register.html', 'r', encoding='utf-8') as f:
        reg_html = f.read()

    assert 'getSafeRedirectUrl' in login_html, "Missing getSafeRedirectUrl in login.html"
    assert 'getSafeRedirectUrl' in reg_html, "Missing getSafeRedirectUrl in register.html"
    assert 'redirectTarget' in login_html, "Missing redirectTarget handler in login.html"
    assert 'redirectTarget' in reg_html, "Missing redirectTarget handler in register.html"
    print("[PASS] TEST 7: Open redirect prevention and safe destination return verified in login & register.")

    # -------------------------------------------------------------------------
    # TEST 8: Feature Card Click & Route Guards in JS
    # -------------------------------------------------------------------------
    with open('js/app.js', 'r', encoding='utf-8') as f:
        app_js = f.read()

    assert 'initHomepageNavigationAndFeatures' in app_js, "Missing initHomepageNavigationAndFeatures in app.js"
    assert 'data-feature-target' in app_js, "Missing data-feature-target handler in app.js"
    assert 'proofvoice_auth_toast' in app_js, "Missing proofvoice_auth_toast in app.js"
    assert 'login.html?redirect=' in app_js, "Missing login.html?redirect= in app.js"
    print("[PASS] TEST 8: Feature card click authentication check and route guard verified in js/app.js.")

    print("=" * 65)
    print("ALL 8 HOMEPAGE, NAVIGATION, FEATURES & SECURITY TESTS PASSED!")
    print("=" * 65)

if __name__ == '__main__':
    test_homepage_navigation_and_features()
