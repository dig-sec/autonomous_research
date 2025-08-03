"""
Basic test script for AcademicSources research modules.
"""
import sys
import os
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))
from autonomous_research.research.academic_sources import AcademicSources

if __name__ == "__main__":
    ac = AcademicSources()
    print("Testing arXiv fetch...")
    arxiv_results = ac.fetch_arxiv("security", max_results=3)
    print(f"arXiv results: {arxiv_results}\n")
    # IEEE Xplore test archived: No API key available
    # print("Testing IEEE Xplore fetch (API key required)...")
    # Replace 'YOUR_API_KEY' with a valid IEEE Xplore API key for real test
    # ieee_results = ac.fetch_ieee_xplore("security", api_key="YOUR_API_KEY", max_records=3)
    # print(f"IEEE Xplore results: {ieee_results}\n")
    ieee_results = []  # Archived: No API key
    print("Testing Google Scholar fetch...")
    scholar_results = ac.fetch_google_scholar("security", max_results=3)
    print(f"Google Scholar results: {scholar_results}\n")
    print("Testing normalization/scoring...")
    normalized = ac.normalize_results(arxiv_results + ieee_results + scholar_results, query="security")
    print(f"Normalized results: {normalized}\n")
