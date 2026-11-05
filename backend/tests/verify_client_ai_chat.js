// -*- coding: utf-8 -*-
/**
 * Verifies client-side ai-chat fallback in js/api-client.js.
 * Guarantees that even if the backend is unreachable, general questions
 * receive educational explanations and NEVER trigger complaint diagnostics.
 */

const fs = require('fs');
const path = require('path');

// Mock localStorage and window
global.localStorage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {}
};
global.window = {
  proofVoiceDb: null
};

// Load api-client.js
const apiClientCode = fs.readFileSync(path.join(__dirname, '../../js/api-client.js'), 'utf-8');
eval(apiClientCode);

const api = window.proofVoiceApi;

const testCases = [
  {
    id: "Client TEST 1",
    query: "What is computer network?",
    lang: "en-IN",
    mustContain: ["network", "interconnected", "LAN"],
    mustNotContain: ["Recommended Category", "Assigned Department", "Suggested Priority"]
  },
  {
    id: "Client TEST 2",
    query: "What is IT?",
    lang: "en-IN",
    mustContain: ["Information Technology", "computers"],
    mustNotContain: ["Recommended Category", "Assigned Department"]
  },
  {
    id: "Client TEST 3",
    query: "Explain Python programming.",
    lang: "en-IN",
    mustContain: ["Python", "high-level", "Guido van Rossum"],
    mustNotContain: ["Recommended Category", "Assigned Department"]
  },
  {
    id: "Client TEST 4",
    query: "How does Wi-Fi work?",
    lang: "en-IN",
    mustContain: ["radio", "frequency", "router"],
    mustNotContain: ["Recommended Category", "Assigned Department"]
  },
  {
    id: "Client TEST 5",
    query: "How do I change my ProofVoice password?",
    lang: "en-IN",
    mustContain: ["Profile & Settings", "Change Password"],
    mustNotContain: ["Recommended Category", "Assigned Department"]
  },
  {
    id: "Client TEST 7",
    query: "My classroom projector is broken. I want to report it.",
    lang: "en-IN",
    mustContain: ["Recommended Category", "Assigned Department"],
    mustNotContain: []
  },
  {
    id: "Client TEST 9",
    query: "मुझे कंप्यूटर नेटवर्क समझाओ।",
    lang: "hi-IN",
    mustContain: ["कंप्यूटर नेटवर्क", "LAN", "राउटर"],
    mustNotContain: ["अनुशंसित श्रेणी", "संबंधित विभाग"]
  },
  {
    id: "Client TEST 10",
    query: "What is TCP? Explain it in simple words.",
    lang: "en-IN",
    mustContain: ["Transmission Control Protocol", "reliable"],
    mustNotContain: ["Recommended Category", "Assigned Department"]
  },
  {
    id: "Client TEST 12",
    query: "Write a Python program to check prime numbers.",
    lang: "en-IN",
    mustContain: ["is_prime", "python"],
    mustNotContain: ["Recommended Category", "Assigned Department"]
  },
  {
    id: "Client TEST 13",
    query: "What is the capital of Japan?",
    lang: "en-IN",
    mustContain: ["Tokyo"],
    mustNotContain: ["Recommended Category", "Assigned Department"]
  },
  {
    id: "Client TEST 16",
    query: "What is a projector?",
    lang: "en-IN",
    mustContain: ["projector", "optical", "screen"],
    mustNotContain: ["Recommended Category", "Assigned Department"]
  },
  {
    id: "Client TEST 17",
    query: "how to sign out ?",
    lang: "en-IN",
    mustContain: ["Sign Out", "sidebar"],
    mustNotContain: ["Recommended Category", "Assigned Department"]
  }
];

console.log("==================================================");
console.log("RUNNING CLIENT-SIDE AI CHAT VERIFICATION (Node.js)");
console.log("==================================================");

let passed = 0;
for (const tc of testCases) {
  const res = api._localAiChatFallback(tc.query, [], false, tc.lang);
  const reply = res.reply || "";

  const missing = tc.mustContain.filter(kw => !reply.toLowerCase().includes(kw.toLowerCase()));
  if (missing.length > 0) {
    console.error(`[FAIL] ${tc.id}: Query '${tc.query}' missing keywords:`, missing);
    console.error("       Reply:", reply.slice(0, 150));
    continue;
  }

  const forbidden = tc.mustNotContain.filter(kw => reply.toLowerCase().includes(kw.toLowerCase()));
  if (forbidden.length > 0) {
    console.error(`[FAIL] ${tc.id}: Query '${tc.query}' contains forbidden complaint keywords:`, forbidden);
    console.error("       Reply:", reply.slice(0, 150));
    continue;
  }

  console.log(`[PASS] ${tc.id}: '${tc.query}' -> topic: ${res.topic}`);
  passed++;
}

console.log("==================================================");
console.log(`CLIENT RESULTS: ${passed}/${testCases.length} PASSED!`);
console.log("==================================================");

if (passed !== testCases.length) {
  process.exit(1);
}
