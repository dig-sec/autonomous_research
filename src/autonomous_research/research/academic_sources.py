"""
Academic Sources Integration for Autonomous Research System

Implements connectors for arXiv, IEEE Xplore, and Google Scholar to fetch security research papers and conference proceedings.
"""

"""
arXiv API integration: Fetches and parses security research papers from arXiv using its public API.
IEEE Xplore API integration: Connects to IEEE Xplore for conference papers (API key required).
Google Scholar scraping: Searches and parses Google Scholar results (rate-limited and respectful scraping).
"""

class AcademicSources:
    def __init__(self, enable_google_scholar=False):
        """
        Initialize Academic Sources.
        
        Args:
            enable_google_scholar (bool): Whether to enable Google Scholar (disabled by default due to blocking issues)
        """
        self.enable_google_scholar = enable_google_scholar
    
    def fetch_arxiv(self, query, max_results=10):
        """
        Fetch security research papers from arXiv using its public API.
        Args:
            query (str): Search query
            max_results (int): Number of results to fetch
        Returns:
            List[dict]: List of normalized paper metadata
        """
        import requests
        import xml.etree.ElementTree as ET
        url = f"http://export.arxiv.org/api/query?search_query={query}&start=0&max_results={max_results}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            root = ET.fromstring(response.text)
            papers = []
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
                link_elem = entry.find('{http://www.w3.org/2005/Atom}id')
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                summary = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else ""
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                authors = []
                for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
                    name_elem = author.find('{http://www.w3.org/2005/Atom}name')
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text.strip())
                papers.append({
                    'title': title,
                    'summary': summary,
                    'link': link,
                    'authors': authors
                })
            return papers
        except Exception as e:
            print(f"arXiv fetch error: {e}")
            return []
    
    def fetch_ieee_xplore(self, query, api_key, max_records=10):
        """
        Fetch conference papers from IEEE Xplore using its API.
        Args:
            query (str): Search query
            api_key (str): IEEE Xplore API key
            max_records (int): Number of records to fetch
        Returns:
            List[dict]: List of normalized paper metadata
        """
        # Example endpoint: https://ieeexploreapi.ieee.org/api/v1/search/articles?apikey=API_KEY&querytext=QUERY&max_records=10
        import requests
        url = f"https://ieeexploreapi.ieee.org/api/v1/search/articles?apikey={api_key}&querytext={query}&max_records={max_records}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            papers = []
            for article in data.get('articles', []):
                title = article.get('title', '')
                abstract = article.get('abstract', '')
                link = article.get('pdf_url', article.get('html_url', ''))
                authors = [a.get('full_name', '') for a in article.get('authors', {}).get('authors', [])]
                papers.append({
                    'title': title,
                    'summary': abstract,
                    'link': link,
                    'authors': authors
                })
            return papers
        except Exception as e:
            print(f"IEEE Xplore fetch error: {e}")
            return []
    
    def fetch_google_scholar(self, query, max_results=10):
        """
        Search Google Scholar for security research papers.
        Simple implementation - try once, if any issue, return empty and move on.
        """
        if not self.enable_google_scholar:
            print("Google Scholar disabled to avoid rate limiting.")
            return []
            
        try:
            from scholarly import scholarly
        except ImportError:
            print("scholarly package not installed. Install with: pip install scholarly")
            return []

        try:
            print(f"Trying Google Scholar for: {query[:50]}...")
            search_query = scholarly.search_pubs(query)
            papers = []
            
            # Try to get results, but don't wait if it hangs
            count = 0
            for pub in search_query:
                if count >= max_results:
                    break
                title = pub.get('bib', {}).get('title', '')
                summary = pub.get('bib', {}).get('abstract', '')
                link = pub.get('pub_url', '')
                authors_raw = pub.get('bib', {}).get('author', '')
                
                if isinstance(authors_raw, list):
                    authors = [str(a).strip() for a in authors_raw]
                elif isinstance(authors_raw, str):
                    authors = [a.strip() for a in authors_raw.split(' and ')] if authors_raw else []
                else:
                    authors = []
                    
                papers.append({
                    'title': title,
                    'summary': summary,
                    'link': link,
                    'authors': authors
                })
                count += 1
                
            print(f"Google Scholar returned {len(papers)} papers")
            return papers
            
        except Exception as e:
            print(f"Google Scholar failed for '{query[:30]}...' - {str(e)[:100]}... Moving on.")
            return []
    
    def fetch_all_sources(self, query, max_results_per_source=10):
        """
        Fetch academic papers from all available sources.
        Prioritizes reliable sources and skips problematic ones.
        """
        all_papers = []
        
        # IEEE Xplore - reliable
        print(f"Fetching from IEEE Xplore for: {query}")
        ieee_papers = self.fetch_ieee_xplore(query, max_results_per_source)
        all_papers.extend(ieee_papers)
        
        # arXiv - reliable  
        print(f"Fetching from arXiv for: {query}")
        arxiv_papers = self.fetch_arxiv(query, max_results_per_source)
        all_papers.extend(arxiv_papers)
        
        # Google Scholar - only if enabled (often blocked)
        if self.enable_google_scholar:
            print(f"Attempting Google Scholar for: {query}")
            scholar_papers = self.fetch_google_scholar(query, max_results_per_source)
            all_papers.extend(scholar_papers)
        else:
            print("Google Scholar disabled (often blocked)")
            
        # Normalize and score all results
        normalized_papers = self.normalize_results(all_papers, query)
        
        print(f"Total papers found: {len(normalized_papers)}")
        return normalized_papers
    
    def normalize_results(self, results, query=None):
        """
        Normalize and score results for relevance and authority.
        Args:
            results (List[dict]): List of paper metadata
            query (str, optional): Search query for relevance scoring
        Returns:
            List[dict]: List of papers with added 'score' field
        """
        normalized = []
        for paper in results:
            score = 0.0
            # Simple relevance: query keyword in title or summary
            if query:
                q = query.lower()
                if q in paper.get('title', '').lower():
                    score += 0.5
                if q in paper.get('summary', '').lower():
                    score += 0.3
            # Authority: more authors, longer summary
            score += min(0.2, len(paper.get('authors', [])) * 0.05)
            score += min(0.2, len(paper.get('summary', '')) / 5000)
            paper['score'] = round(score, 3)
            normalized.append(paper)
        # Sort by score descending
        normalized.sort(key=lambda x: x['score'], reverse=True)
        return normalized
