#!/bin/bash

# Enhanced RAG System - Dependency Installation Script
# Installs all required packages for the enhanced RAG system with Elasticsearch support

echo "🚀 Installing Enhanced RAG System Dependencies..."
echo "================================================="

# Core scientific computing
echo "📦 Installing core scientific packages..."
pip install numpy scipy scikit-learn

# Embedding and similarity
echo "🧠 Installing embedding and similarity packages..."
pip install sentence-transformers transformers torch

# Elasticsearch support (NEW)
echo "🔍 Installing Elasticsearch client..."
pip install elasticsearch

# Legacy vector database support (optional)
echo "🗂️  Installing vector database packages..."
pip install faiss-cpu  # Use faiss-gpu if you have CUDA
pip install chromadb

# Document processing
echo "📄 Installing document processing packages..."
pip install PyPDF2 pdfplumber  # PDF processing
pip install beautifulsoup4 lxml  # HTML processing
pip install python-docx  # Word documents
pip install openpyxl  # Excel files
pip install markdown  # Markdown processing

# Data handling and utilities
echo "🛠️  Installing utility packages..."
pip install pandas
pip install requests
pip install tqdm  # Progress bars
pip install python-dotenv  # Environment variables

# Optional: Advanced NLP
echo "🔤 Installing advanced NLP packages..."
pip install spacy
pip install nltk

# Optional: Plotting and visualization
echo "📊 Installing visualization packages..."
pip install matplotlib seaborn plotly

echo ""
echo "✅ RAG Dependencies Installation Complete!"
echo ""
echo "📋 Summary of installed packages:"
echo "   ✓ numpy, scipy, scikit-learn (core scientific computing)"
echo "   ✓ sentence-transformers, torch (embeddings)"
echo "   ✓ elasticsearch (primary vector database)"
echo "   ✓ faiss-cpu, chromadb (alternative vector databases)"
echo "   ✓ PyPDF2, beautifulsoup4, python-docx (document processing)"
echo "   ✓ pandas, requests, tqdm (utilities)"
echo "   ✓ spacy, nltk (advanced NLP)"
echo "   ✓ matplotlib, seaborn, plotly (visualization)"
echo ""
echo "🎯 Next steps:"
echo "   1. Ensure Elasticsearch is running on localhost:9200"
echo "   2. Test the RAG system: python3 src/autonomous_research/rag/elasticsearch_db.py"
echo "   3. Use the StandaloneElasticsearchRAG class for your RAG needs"
echo ""
echo "🔧 Elasticsearch Configuration:"
echo "   Host: localhost:9200"
echo "   Credentials: Set ES_USER and ES_PASSWORD in your .env file or environment variables."
echo ""
