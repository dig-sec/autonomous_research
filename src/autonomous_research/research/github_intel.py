"""
GitHub Intelligence Module

Implements enhanced repository analysis and security-focused research
from GitHub repositories using the GitHub API v4 (GraphQL).

Based on PROJECT_TODO Phase 2.1 - GitHub Intelligence Module
"""

import requests
import time
import json
import base64
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import re


class GitHubIntelligence:
    """
    Enhanced GitHub repository analysis for security research.
    
    Features:
    - Repository quality scoring (stars, forks, activity)
    - README and documentation extraction
    - Code analysis for security implementations
    - Proof-of-concept identification
    - Security framework alignment detection
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub Intelligence module.
        
        Args:
            github_token: Optional GitHub personal access token for higher rate limits
        """
        self.github_token = github_token
        self.session = requests.Session()
        
        # Set up headers
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AutonomousResearch-SecurityIntel/1.0'
        }
        
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
            print("✅ GitHub Intelligence initialized with authentication")
        else:
            print("⚠️  GitHub Intelligence initialized without token (rate limited)")
        
        # API endpoints
        self.api_base = "https://api.github.com"
        self.graphql_url = "https://api.github.com/graphql"
        
        # Security keywords for repository filtering
        self.security_keywords = {
            'mitre_attack': ['mitre', 'att&ck', 'attack', 'technique', 'tactic'],
            'penetration_testing': ['pentest', 'pentesting', 'red team', 'redteam', 'exploit'],
            'malware_analysis': ['malware', 'reverse engineering', 'analysis', 'forensics'],
            'vulnerability': ['vulnerability', 'cve', 'exploit', 'poc', 'proof of concept'],
            'detection': ['detection', 'hunting', 'sigma', 'yara', 'snort'],
            'incident_response': ['incident response', 'ir', 'dfir', 'forensics'],
            'threat_intelligence': ['threat intel', 'tti', 'ioc', 'indicator'],
            'security_tools': ['security tool', 'infosec', 'cybersec', 'netsec']
        }
        
        # Language priorities for security research
        self.language_priorities = {
            'PowerShell': 10,
            'Python': 9,
            'C#': 8,
            'C++': 8,
            'C': 8,
            'JavaScript': 7,
            'Go': 7,
            'Rust': 7,
            'Ruby': 6,
            'PHP': 5,
            'Java': 5,
            'Shell': 9,
            'Batch': 6
        }

    def search_security_repositories(
        self,
        query: str,
        technique_id: Optional[str] = None,
        language: Optional[str] = None,
        min_stars: int = 5,
        max_results: int = 30
    ) -> List[Dict]:
        """
        Search for security-related repositories on GitHub.
        
        Args:
            query: Search query (technique name, security topic, etc.)
            technique_id: Optional MITRE ATT&CK technique ID (e.g., "T1003")
            language: Optional programming language filter
            min_stars: Minimum number of stars
            max_results: Maximum number of results to return
            
        Returns:
            List of repository information dictionaries
        """
        
        print(f"🔍 Searching GitHub for: {query}")
        if technique_id:
            print(f"   🎯 MITRE ATT&CK: {technique_id}")
        
        # Build search query
        search_terms = [query]
        
        if technique_id:
            search_terms.extend([technique_id, technique_id.replace('T', 'T-')])
        
        # Add security context
        security_context = ['security', 'cybersecurity', 'infosec']
        
        # GitHub search API parameters
        search_params = {
            'q': f"{' OR '.join(search_terms)} {' OR '.join(security_context)} stars:>={min_stars}",
            'sort': 'stars',
            'order': 'desc',
            'per_page': min(max_results, 100)
        }
        
        if language:
            search_params['q'] += f" language:{language}"
        
        try:
            response = self.session.get(
                f"{self.api_base}/search/repositories",
                headers=self.headers,
                params=search_params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                repositories = []
                
                for repo in data.get('items', [])[:max_results]:
                    repo_info = self._extract_repository_info(repo)
                    
                    # Calculate security relevance score
                    repo_info['security_score'] = self._calculate_security_score(repo_info, query, technique_id)
                    
                    repositories.append(repo_info)
                
                # Sort by security relevance
                repositories.sort(key=lambda x: x['security_score'], reverse=True)
                
                print(f"✅ Found {len(repositories)} relevant repositories")
                return repositories
                
            elif response.status_code == 403:
                print("❌ GitHub API rate limit exceeded")
                return []
            else:
                print(f"❌ GitHub API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching GitHub: {e}")
            return []

    def analyze_repository(self, repo_url: str) -> Dict:
        """
        Perform detailed analysis of a specific repository.
        
        Args:
            repo_url: GitHub repository URL or owner/repo format
            
        Returns:
            Detailed repository analysis
        """
        
        # Parse repository owner and name
        owner, repo_name = self._parse_repo_url(repo_url)
        if not owner or not repo_name:
            return {'error': 'Invalid repository URL'}
        
        print(f"🔬 Analyzing repository: {owner}/{repo_name}")
        
        # Get repository details
        repo_details = self._get_repository_details(owner, repo_name)
        if 'error' in repo_details:
            return repo_details
        
        # Analyze README and documentation
        documentation = self._analyze_documentation(owner, repo_name)
        
        # Analyze repository structure and code
        code_analysis = self._analyze_code_structure(owner, repo_name)
        
        # Look for security-specific files
        security_files = self._find_security_files(owner, repo_name)
        
        # Calculate comprehensive scores
        quality_score = self._calculate_repository_quality(repo_details)
        security_relevance = self._calculate_detailed_security_relevance(
            repo_details, documentation, code_analysis, security_files
        )
        
        return {
            'repository': repo_details,
            'documentation': documentation,
            'code_analysis': code_analysis,
            'security_files': security_files,
            'scores': {
                'quality_score': quality_score,
                'security_relevance': security_relevance,
                'overall_score': (quality_score + security_relevance) / 2
            },
            'analysis_timestamp': time.time()
        }

    def extract_technique_implementations(
        self,
        repo_url: str,
        technique_id: str
    ) -> List[Dict]:
        """
        Extract specific technique implementations from a repository.
        
        Args:
            repo_url: GitHub repository URL
            technique_id: MITRE ATT&CK technique ID
            
        Returns:
            List of technique implementation details
        """
        
        owner, repo_name = self._parse_repo_url(repo_url)
        if not owner or not repo_name:
            return []
        
        print(f"🎯 Extracting {technique_id} implementations from {owner}/{repo_name}")
        
        implementations = []
        
        # Search for files mentioning the technique
        technique_files = self._search_repository_content(
            owner, repo_name, technique_id
        )
        
        for file_info in technique_files:
            # Analyze file content for implementation details
            implementation = self._analyze_technique_file(
                owner, repo_name, file_info, technique_id
            )
            
            if implementation:
                implementations.append(implementation)
        
        print(f"✅ Found {len(implementations)} {technique_id} implementations")
        return implementations

    def _extract_repository_info(self, repo_data: Dict) -> Dict:
        """Extract and standardize repository information from GitHub API response."""
        
        return {
            'name': repo_data.get('name', ''),
            'full_name': repo_data.get('full_name', ''),
            'owner': repo_data.get('owner', {}).get('login', ''),
            'description': repo_data.get('description', ''),
            'url': repo_data.get('html_url', ''),
            'clone_url': repo_data.get('clone_url', ''),
            'language': repo_data.get('language', ''),
            'languages_url': repo_data.get('languages_url', ''),
            'stars': repo_data.get('stargazers_count', 0),
            'forks': repo_data.get('forks_count', 0),
            'watchers': repo_data.get('watchers_count', 0),
            'open_issues': repo_data.get('open_issues_count', 0),
            'size': repo_data.get('size', 0),
            'created_at': repo_data.get('created_at', ''),
            'updated_at': repo_data.get('updated_at', ''),
            'pushed_at': repo_data.get('pushed_at', ''),
            'default_branch': repo_data.get('default_branch', 'main'),
            'topics': repo_data.get('topics', []),
            'license': repo_data.get('license', {}).get('name', '') if repo_data.get('license') else '',
            'archived': repo_data.get('archived', False),
            'disabled': repo_data.get('disabled', False)
        }

    def _calculate_security_score(self, repo_info: Dict, query: str, technique_id: Optional[str]) -> float:
        """Calculate security relevance score for a repository."""
        
        score = 0.0
        
        # Base popularity score (0-30 points)
        popularity_score = min(30, repo_info['stars'] / 10)
        score += popularity_score
        
        # Language relevance (0-20 points)
        language = repo_info.get('language', '')
        if language in self.language_priorities:
            score += self.language_priorities[language] * 2
        
        # Description and name analysis (0-30 points)
        text_to_analyze = f"{repo_info.get('description', '')} {repo_info.get('name', '')}"
        text_lower = text_to_analyze.lower()
        
        # Query term matching
        query_terms = query.lower().split()
        for term in query_terms:
            if term in text_lower:
                score += 5
        
        # Technique ID matching
        if technique_id and technique_id.lower() in text_lower:
            score += 15
        
        # Security keyword matching
        for category, keywords in self.security_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    score += 3
                    break  # Only count once per category
        
        # Topics matching (0-10 points)
        topics = repo_info.get('topics', [])
        security_topics = ['security', 'cybersecurity', 'infosec', 'pentest', 'malware', 'mitre']
        for topic in topics:
            if any(sec_topic in topic.lower() for sec_topic in security_topics):
                score += 2
        
        # Recent activity bonus (0-10 points)
        if repo_info.get('pushed_at'):
            try:
                from datetime import datetime, timezone
                pushed_date = datetime.fromisoformat(repo_info['pushed_at'].replace('Z', '+00:00'))
                days_since_update = (datetime.now(timezone.utc) - pushed_date).days
                
                if days_since_update < 30:
                    score += 10
                elif days_since_update < 90:
                    score += 5
                elif days_since_update < 365:
                    score += 2
            except:
                pass
        
        return min(100, score)  # Cap at 100

    def _parse_repo_url(self, repo_url: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse repository URL to extract owner and repository name."""
        
        # Handle different URL formats
        if repo_url.startswith('https://github.com/'):
            parts = repo_url.replace('https://github.com/', '').strip('/').split('/')
            if len(parts) >= 2:
                return parts[0], parts[1]
        elif '/' in repo_url and not repo_url.startswith('http'):
            # Direct owner/repo format
            parts = repo_url.split('/')
            if len(parts) == 2:
                return parts[0], parts[1]
        
        return None, None

    def _get_repository_details(self, owner: str, repo_name: str) -> Dict:
        """Get detailed repository information from GitHub API."""
        
        try:
            response = self.session.get(
                f"{self.api_base}/repos/{owner}/{repo_name}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return self._extract_repository_info(response.json())
            elif response.status_code == 404:
                return {'error': 'Repository not found'}
            elif response.status_code == 403:
                return {'error': 'API rate limit exceeded'}
            else:
                return {'error': f'API error: {response.status_code}'}
                
        except Exception as e:
            return {'error': f'Request failed: {e}'}

    def _analyze_documentation(self, owner: str, repo_name: str) -> Dict:
        """Analyze repository documentation (README, etc.)."""
        
        documentation = {
            'readme_content': '',
            'readme_sections': [],
            'technique_mentions': [],
            'security_frameworks': [],
            'installation_instructions': False,
            'usage_examples': False
        }
        
        # Get README content
        readme_files = ['README.md', 'README.txt', 'README.rst', 'README']
        
        for readme_file in readme_files:
            try:
                response = self.session.get(
                    f"{self.api_base}/repos/{owner}/{repo_name}/contents/{readme_file}",
                    headers=self.headers,
                    timeout=15
                )
                
                if response.status_code == 200:
                    file_data = response.json()
                    if file_data.get('content'):
                        # Decode base64 content
                        content = base64.b64decode(file_data['content']).decode('utf-8', errors='ignore')
                        documentation['readme_content'] = content
                        
                        # Analyze README content
                        documentation.update(self._analyze_readme_content(content))
                        break
                        
            except Exception as e:
                continue
        
        return documentation

    def _analyze_readme_content(self, content: str) -> Dict:
        """Analyze README content for security-relevant information."""
        
        content_lower = content.lower()
        
        # Extract sections (markdown headers)
        sections = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        
        # Look for technique mentions (T1001, T1003, etc.)
        technique_mentions = re.findall(r'\bT\d{4}(?:\.\d{3})?\b', content, re.IGNORECASE)
        
        # Identify security frameworks
        frameworks = []
        framework_keywords = {
            'MITRE ATT&CK': ['mitre', 'att&ck', 'attack'],
            'NIST': ['nist'],
            'OWASP': ['owasp'],
            'SANS': ['sans'],
            'CIS': ['cis controls', 'cis benchmark']
        }
        
        for framework, keywords in framework_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                frameworks.append(framework)
        
        # Check for installation and usage
        installation_keywords = ['install', 'setup', 'requirements', 'dependencies']
        usage_keywords = ['usage', 'example', 'how to', 'getting started']
        
        has_installation = any(keyword in content_lower for keyword in installation_keywords)
        has_usage = any(keyword in content_lower for keyword in usage_keywords)
        
        return {
            'readme_sections': sections,
            'technique_mentions': list(set(technique_mentions)),
            'security_frameworks': frameworks,
            'installation_instructions': has_installation,
            'usage_examples': has_usage
        }

    def _analyze_code_structure(self, owner: str, repo_name: str) -> Dict:
        """Analyze repository code structure and identify security-relevant files."""
        
        code_analysis = {
            'languages': {},
            'file_count': 0,
            'security_files': [],
            'script_files': [],
            'config_files': [],
            'documentation_files': []
        }
        
        try:
            # Get repository languages
            response = self.session.get(
                f"{self.api_base}/repos/{owner}/{repo_name}/languages",
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                code_analysis['languages'] = response.json()
            
            # Get repository tree (first level)
            tree_response = self.session.get(
                f"{self.api_base}/repos/{owner}/{repo_name}/git/trees/HEAD",
                headers=self.headers,
                timeout=15
            )
            
            if tree_response.status_code == 200:
                tree_data = tree_response.json()
                
                for item in tree_data.get('tree', []):
                    if item['type'] == 'blob':  # File
                        file_path = item['path']
                        code_analysis['file_count'] += 1
                        
                        # Categorize files
                        self._categorize_file(file_path, code_analysis)
            
        except Exception as e:
            print(f"⚠️  Code analysis error: {e}")
        
        return code_analysis

    def _categorize_file(self, file_path: str, analysis: Dict):
        """Categorize a file based on its path and extension."""
        
        file_lower = file_path.lower()
        
        # Security-related files
        security_patterns = [
            'exploit', 'payload', 'attack', 'technique', 'mitre',
            'vuln', 'poc', 'proof', 'malware', 'trojan', 'backdoor'
        ]
        
        if any(pattern in file_lower for pattern in security_patterns):
            analysis['security_files'].append(file_path)
        
        # Script files
        script_extensions = ['.ps1', '.py', '.sh', '.bat', '.cmd', '.rb', '.pl']
        if any(file_lower.endswith(ext) for ext in script_extensions):
            analysis['script_files'].append(file_path)
        
        # Configuration files
        config_patterns = ['config', 'conf', '.yml', '.yaml', '.json', '.xml', '.ini']
        if any(pattern in file_lower for pattern in config_patterns):
            analysis['config_files'].append(file_path)
        
        # Documentation files
        doc_patterns = ['.md', '.txt', '.rst', 'readme', 'doc', 'manual']
        if any(pattern in file_lower for pattern in doc_patterns):
            analysis['documentation_files'].append(file_path)

    def _find_security_files(self, owner: str, repo_name: str) -> List[Dict]:
        """Find and analyze security-specific files in the repository."""
        
        security_files = []
        
        # Common security file patterns
        security_patterns = [
            'exploit', 'payload', 'attack', 'technique', 
            'sigma', 'yara', 'snort', 'suricata',
            'ioc', 'indicator', 'rule'
        ]
        
        # Search for security files
        for pattern in security_patterns:
            try:
                response = self.session.get(
                    f"{self.api_base}/search/code",
                    headers=self.headers,
                    params={
                        'q': f'{pattern} repo:{owner}/{repo_name}',
                        'per_page': 10
                    },
                    timeout=15
                )
                
                if response.status_code == 200:
                    results = response.json()
                    for item in results.get('items', []):
                        security_files.append({
                            'file_path': item.get('path', ''),
                            'pattern_match': pattern,
                            'url': item.get('html_url', ''),
                            'score': item.get('score', 0)
                        })
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                continue
        
        return security_files

    def _search_repository_content(self, owner: str, repo_name: str, search_term: str) -> List[Dict]:
        """Search for specific content within a repository."""
        
        files = []
        
        try:
            response = self.session.get(
                f"{self.api_base}/search/code",
                headers=self.headers,
                params={
                    'q': f'{search_term} repo:{owner}/{repo_name}',
                    'per_page': 30
                },
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                for item in results.get('items', []):
                    files.append({
                        'path': item.get('path', ''),
                        'name': item.get('name', ''),
                        'url': item.get('html_url', ''),
                        'score': item.get('score', 0),
                        'repository': item.get('repository', {})
                    })
        
        except Exception as e:
            print(f"⚠️  Content search error: {e}")
        
        return files

    def _analyze_technique_file(
        self, 
        owner: str, 
        repo_name: str, 
        file_info: Dict, 
        technique_id: str
    ) -> Optional[Dict]:
        """Analyze a specific file for technique implementation details."""
        
        try:
            # Get file content
            response = self.session.get(
                f"{self.api_base}/repos/{owner}/{repo_name}/contents/{file_info['path']}",
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                file_data = response.json()
                if file_data.get('content'):
                    content = base64.b64decode(file_data['content']).decode('utf-8', errors='ignore')
                    
                    # Analyze content for technique implementation
                    return {
                        'file_path': file_info['path'],
                        'file_name': file_info['name'],
                        'file_url': file_info['url'],
                        'technique_id': technique_id,
                        'content_preview': content[:500],
                        'file_size': len(content),
                        'line_count': content.count('\n') + 1,
                        'technique_mentions': content.upper().count(technique_id.upper()),
                        'implementation_type': self._identify_implementation_type(content, file_info['path'])
                    }
        
        except Exception as e:
            print(f"⚠️  File analysis error: {e}")
        
        return None

    def _identify_implementation_type(self, content: str, file_path: str) -> str:
        """Identify the type of security implementation in the file."""
        
        content_lower = content.lower()
        file_lower = file_path.lower()
        
        if any(ext in file_lower for ext in ['.ps1', '.bat', '.cmd']):
            if 'invoke-' in content_lower or 'get-' in content_lower:
                return 'PowerShell Tool'
            else:
                return 'PowerShell Script'
        elif file_lower.endswith('.py'):
            if 'class ' in content_lower and 'def ' in content_lower:
                return 'Python Tool/Library'
            else:
                return 'Python Script'
        elif any(keyword in content_lower for keyword in ['exploit', 'payload', 'shellcode']):
            return 'Exploit/Payload'
        elif any(keyword in content_lower for keyword in ['rule', 'detection', 'sigma', 'yara']):
            return 'Detection Rule'
        elif any(keyword in content_lower for keyword in ['documentation', 'readme', 'guide']):
            return 'Documentation'
        else:
            return 'Code Implementation'

    def _calculate_repository_quality(self, repo_info: Dict) -> float:
        """Calculate overall repository quality score."""
        
        score = 0.0
        
        # Stars (0-30 points)
        stars = repo_info.get('stars', 0)
        score += min(30, stars / 10)
        
        # Forks (0-15 points)
        forks = repo_info.get('forks', 0)
        score += min(15, forks / 5)
        
        # Activity (0-20 points)
        if repo_info.get('pushed_at'):
            try:
                from datetime import datetime, timezone
                pushed_date = datetime.fromisoformat(repo_info['pushed_at'].replace('Z', '+00:00'))
                days_since_update = (datetime.now(timezone.utc) - pushed_date).days
                
                if days_since_update < 7:
                    score += 20
                elif days_since_update < 30:
                    score += 15
                elif days_since_update < 90:
                    score += 10
                elif days_since_update < 365:
                    score += 5
            except:
                pass
        
        # Has description (0-10 points)
        if repo_info.get('description', '').strip():
            score += 10
        
        # Has license (0-10 points)
        if repo_info.get('license'):
            score += 10
        
        # Size reasonable (0-10 points)
        size = repo_info.get('size', 0)
        if 100 <= size <= 10000:  # Sweet spot for tools
            score += 10
        elif size > 0:
            score += 5
        
        # Not archived/disabled (0-5 points)
        if not repo_info.get('archived', False) and not repo_info.get('disabled', False):
            score += 5
        
        return min(100, score)

    def _calculate_detailed_security_relevance(
        self, 
        repo_info: Dict, 
        documentation: Dict, 
        code_analysis: Dict, 
        security_files: List[Dict]
    ) -> float:
        """Calculate detailed security relevance score."""
        
        score = 0.0
        
        # Security keywords in description (0-20 points)
        description = repo_info.get('description', '').lower()
        security_matches = sum(1 for keywords in self.security_keywords.values() 
                             for keyword in keywords if keyword in description)
        score += min(20, security_matches * 2)
        
        # MITRE technique mentions in docs (0-25 points)
        technique_mentions = len(documentation.get('technique_mentions', []))
        score += min(25, technique_mentions * 5)
        
        # Security frameworks mentioned (0-20 points)
        frameworks = len(documentation.get('security_frameworks', []))
        score += min(20, frameworks * 5)
        
        # Security-related files (0-20 points)
        security_file_count = len(security_files)
        score += min(20, security_file_count * 2)
        
        # Programming languages (0-15 points)
        languages = code_analysis.get('languages', {})
        for lang, priority in self.language_priorities.items():
            if lang in languages:
                score += min(15, priority)
                break
        
        return min(100, score)


def test_github_intelligence():
    """Test GitHub Intelligence functionality."""
    
    print("🧪 Testing GitHub Intelligence")
    print("=" * 50)
    
    # Initialize (without token for testing)
    github_intel = GitHubIntelligence()
    
    # Test repository search
    print("\n🔍 Testing Repository Search:")
    repos = github_intel.search_security_repositories(
        "credential dumping",
        technique_id="T1003",
        max_results=5
    )
    
    for i, repo in enumerate(repos[:3], 1):
        print(f"  {i}. {repo['full_name']} (⭐{repo['stars']}) - Score: {repo['security_score']:.1f}")
        print(f"     {repo['description'][:100]}...")
    
    # Test detailed repository analysis
    if repos:
        print(f"\n🔬 Testing Detailed Analysis:")
        analysis = github_intel.analyze_repository(repos[0]['full_name'])
        
        if 'error' not in analysis:
            print(f"  Repository: {repos[0]['full_name']}")
            print(f"  Quality Score: {analysis['scores']['quality_score']:.1f}")
            print(f"  Security Relevance: {analysis['scores']['security_relevance']:.1f}")
            print(f"  Overall Score: {analysis['scores']['overall_score']:.1f}")
            
            # Show documentation insights
            doc = analysis['documentation']
            if doc['technique_mentions']:
                print(f"  Technique Mentions: {', '.join(doc['technique_mentions'])}")
            if doc['security_frameworks']:
                print(f"  Security Frameworks: {', '.join(doc['security_frameworks'])}")
        else:
            print(f"  ❌ Analysis failed: {analysis['error']}")


if __name__ == "__main__":
    test_github_intelligence()
