# -*- coding: utf-8 -*-
"""
Web Search & Real-Time Information Retrieval Service.
Integrates Serper, Tavily, DuckDuckGo Instant Answers, and Wikipedia APIs
to answer general knowledge, current affairs, and latest technological questions with citations.
"""
import os
import re
import logging
import requests

logger = logging.getLogger(__name__)

WEB_SEARCH_INDICATORS = re.compile(
    r'\b(search|google|internet|latest|current\s*news|today|who\s*is\s*the\s*prime\s*minister|'
    r'who\s*is\s*the\s*president|capital\s*of|weather|score|population|gdp|currency|'
    r'what\s*happened|when\s*was\s*released|history\s*of|discovery\s*of|nobel\s*prize)\b',
    re.IGNORECASE
)

class WebSearchService:
    @classmethod
    def should_search_web(cls, query: str) -> bool:
        """Determines if a query requires live web search."""
        if not query:
            return False
        return bool(WEB_SEARCH_INDICATORS.search(query))

    @classmethod
    def search(cls, query: str, max_results: int = 3) -> dict:
        """
        Executes web search across configured providers with graceful fallbacks.
        Returns a dict: {'success': bool, 'summary': str, 'sources': list, 'source_name': str}
        """
        clean_query = query.strip()
        if not clean_query:
            return {'success': False, 'summary': '', 'sources': []}

        # 1. Try Google Serper API if configured
        serper_key = os.getenv('SERPER_API_KEY', '').strip()
        if serper_key:
            try:
                res = requests.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
                    json={"q": clean_query, "num": max_results},
                    timeout=5
                )
                if res.status_code == 200:
                    data = res.json()
                    organic = data.get('organic', [])
                    if organic:
                        snippets = []
                        sources = []
                        for item in organic[:max_results]:
                            snippets.append(f"• {item.get('title', '')}: {item.get('snippet', '')}")
                            if item.get('link'):
                                sources.append({'title': item.get('title'), 'url': item.get('link')})
                        return {
                            'success': True,
                            'summary': "\n".join(snippets),
                            'sources': sources,
                            'source_name': 'Google Search (Serper)'
                        }
            except Exception as e:
                logger.warning(f"Serper API failed: {e}")

        # 2. Try DuckDuckGo Instant Answer API (Free, Reliable)
        try:
            ddg_url = f"https://api.duckduckgo.com/?q={requests.utils.quote(clean_query)}&format=json&no_html=1&skip_disambig=1"
            res = requests.get(ddg_url, timeout=5, headers={"User-Agent": "ProofVoice-CampusAssistant/1.0"})
            if res.status_code == 200:
                data = res.json()
                abstract = data.get('AbstractText', '').strip()
                heading = data.get('Heading', clean_query)
                source_url = data.get('AbstractURL', '')
                if abstract:
                    sources = [{'title': heading, 'url': source_url}] if source_url else []
                    return {
                        'success': True,
                        'summary': f"**{heading}:** {abstract}",
                        'sources': sources,
                        'source_name': 'DuckDuckGo Knowledge'
                    }
                # Check related topics
                related = data.get('RelatedTopics', [])
                for topic in related:
                    if isinstance(topic, dict) and topic.get('Text'):
                        text = topic.get('Text')
                        url = topic.get('FirstURL', '')
                        sources = [{'title': clean_query, 'url': url}] if url else []
                        return {
                            'success': True,
                            'summary': text,
                            'sources': sources,
                            'source_name': 'DuckDuckGo Instant Answers'
                        }
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")

        # 3. Try Wikipedia Search API
        try:
            wiki_search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={requests.utils.quote(clean_query)}&format=json&utf8=1"
            res = requests.get(wiki_search_url, timeout=5, headers={"User-Agent": "ProofVoice-CampusAssistant/1.0"})
            if res.status_code == 200:
                data = res.json()
                search_results = data.get('query', {}).get('search', [])
                if search_results:
                    top_title = search_results[0].get('title', '')
                    snippet = re.sub(r'<[^>]+>', '', search_results[0].get('snippet', ''))
                    # Get summary
                    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(top_title)}"
                    s_res = requests.get(summary_url, timeout=5, headers={"User-Agent": "ProofVoice-CampusAssistant/1.0"})
                    if s_res.status_code == 200:
                        s_data = s_res.json()
                        extract = s_data.get('extract', snippet)
                        page_url = s_data.get('content_urls', {}).get('desktop', {}).get('page', f"https://en.wikipedia.org/wiki/{top_title}")
                        return {
                            'success': True,
                            'summary': f"**{top_title}**\n\n{extract}",
                            'sources': [{'title': f"Wikipedia: {top_title}", 'url': page_url}],
                            'source_name': 'Wikipedia'
                        }
        except Exception as e:
            logger.warning(f"Wikipedia search failed: {e}")

        return {'success': False, 'summary': '', 'sources': []}
