# Autonomous Research System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-18%2F18%20passing-brightgreen.svg)](tests/)

A comprehensive autonomous system for security research, technique analysis, and documentation generation with AI-driven content creation. This system leverages multiple AI models, open source intelligence, and automated research workflows to provide in-depth cybersecurity analysis.

## 🚀 Features

- **Autonomous Research**: Fully automated research pipeline with AI-driven analysis
- **Multi-Modal AI Integration**: Support for Ollama, OpenAI, and other LLM providers
- **Vector Database RAG**: Elasticsearch-powered retrieval-augmented generation
- **MITRE ATT&CK Integration**: Built-in support for cybersecurity technique analysis
- **Custom Technique Management**: Define and research custom security techniques
- **Research Queue Management**: Elasticsearch-backed research task queuing
- **Comprehensive Reporting**: Automated generation of detailed research reports
- **CLI Interface**: Command-line tools for easy system management
- **Threat Intelligence**: Integration with external threat intelligence feeds

## 📋 Prerequisites

Before setting up the Autonomous Research System, ensure you have:

- **Python 3.8+**
- **Elasticsearch 8.x** (for vector database and queue management)
- **Ollama** (for local LLM inference) or **OpenAI API access**
- **Git** (for version control)
- **Docker** (optional, for containerized deployment)

## 🛠 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/autonomous_research.git
cd autonomous_research
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

Required environment variables:
- `ES_PASSWORD`: Your Elasticsearch password
- `OLLAMA_HOST`: Ollama server URL (default: http://localhost:11434)
- `GITHUB_TOKEN`: GitHub API token (optional, for enhanced research)

### 4. Run Setup Script

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 5. Start Required Services

#### Elasticsearch (via Docker)
```bash
# Start Elasticsearch with proper configuration
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=true" \
  -e "ELASTIC_PASSWORD=your_password" \
  docker.elastic.co/elasticsearch/elasticsearch:8.11.0
```

#### Ollama (Local LLM)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull required models
ollama pull llama2
ollama pull mistral
```

## 🎯 Quick Start

### Check System Status
```bash
python -m cli.status
```

### Run a Quick Research Query
```bash
python -m cli.query "CVE-2023-12345 analysis"
```

### Start the Autonomous Research System
```bash
python -m cli.autonomous
```

### Use the Research Manager
```bash
python -m cli.research_manager --help
```

### Interactive Demo
```bash
python -m cli.quickstart
```

## 🏗 System Architecture

```
autonomous_research/
├── src/autonomous_research/          # Core system modules
│   ├── core/                        # Core system components
│   │   ├── autonomous_system.py     # Main orchestration system
│   │   └── project_manager.py       # Project lifecycle management
│   ├── research/                    # Research pipeline components
│   │   └── summary_manager.py       # Research summarization
│   ├── generation/                  # Content generation
│   │   └── content_generator.py     # AI-powered content creation
│   ├── knowledge/                   # Knowledge management
│   │   └── custom_techniques.py     # Custom technique definitions
│   ├── rag/                        # RAG system components
│   │   └── elasticsearch_db.py      # Vector database operations
│   └── utils/                       # Utility functions
├── cli/                             # Command-line interfaces
│   ├── autonomous.py                # Main autonomous system CLI
│   ├── research_manager.py          # Research management CLI
│   ├── status.py                    # System health checks
│   └── query.py                     # Quick query interface
├── tests/                           # Test suite
│   ├── unit/                        # Unit tests
│   └── integration/                 # Integration tests
├── scripts/                         # Setup and utility scripts
├── docs/                           # Documentation
└── containers/                     # Docker configurations
```

## 🔧 Configuration

### Elasticsearch Configuration
The system requires Elasticsearch 8.x with proper authentication:

```python
# Configuration automatically loaded from .env
ES_HOST=localhost
ES_PORT=9200
ES_USER=elastic
ES_PASSWORD=your_secure_password
```

### AI Model Configuration
Configure your preferred AI providers:

```python
# Ollama (Local)
OLLAMA_HOST=http://localhost:11434

# Rate limiting for external APIs
RATE_LIMIT_GITHUB=1.0
RATE_LIMIT_MITRE=0.5
RATE_LIMIT_WEB=2.0
```

## 📊 Usage Examples

### Autonomous Research Pipeline
```python
from src.autonomous_research import AutonomousResearchSystem

# Initialize the system
system = AutonomousResearchSystem()

# Start autonomous research
await system.run_autonomous_research()
```

### Custom Technique Research
```python
from src.autonomous_research.knowledge.custom_techniques import CustomTechnique

# Define a custom technique
technique = CustomTechnique(
    name="Advanced Persistence Mechanism",
    description="Novel persistence technique analysis",
    mitre_technique="T1547"
)

# Research the technique
results = await system.research_technique(technique)
```

### Query Research Database
```python
# Search existing research
results = await system.search_research("lateral movement techniques")

# Generate new research report
report = await system.generate_report("CVE-2024-1234")
```

## 🧪 Testing

The system includes comprehensive testing:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/ -v          # Unit tests
python -m pytest tests/integration/ -v   # Integration tests

# Run with coverage
python -m pytest tests/ --cov=src/autonomous_research --cov-report=html
```

Current test status: **18/18 tests passing** ✅

## 📈 Monitoring and Debugging

### System Health Check
```bash
python -m cli.status
```

### Debug Elasticsearch Queue
```bash
python -m src.autonomous_research.debug_es_queue
```

### View Logs
```bash
tail -f logs/autonomous_research.log
```

## 🔐 Security Considerations

- **Environment Variables**: All sensitive configuration stored in `.env` (never commit to git)
- **API Rate Limiting**: Built-in rate limiting for external API calls
- **Secure Elasticsearch**: Authentication required for all database operations
- **Input Validation**: All research inputs validated and sanitized
- **Audit Logging**: Comprehensive logging of all research activities

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install

# Run linting
flake8 src/ tests/
black src/ tests/
```

## 📚 Documentation

- **API Documentation**: Available in `docs/api/`
- **Architecture Guide**: See `docs/architecture.md`
- **Configuration Guide**: See `docs/configuration.md`
- **Deployment Guide**: See `docs/deployment.md`

## 🐛 Troubleshooting

### Common Issues

1. **Elasticsearch Connection Errors**
   ```bash
   # Check Elasticsearch status
   curl -u elastic:password http://localhost:9200/_cluster/health
   ```

2. **Ollama Connection Timeout**
   - Increase timeout in configuration (default: 60 seconds)
   - Ensure Ollama service is running: `ollama serve`

3. **Missing Environment Variables**
   - Verify `.env` file exists and contains required variables
   - Source environment: `source .env`

4. **Test Failures**
   - Ensure all services are running (Elasticsearch, Ollama)
   - Check environment variable configuration

### Getting Help

- **Issues**: Report bugs via [GitHub Issues](https://github.com/your-username/autonomous_research/issues)
- **Discussions**: Join [GitHub Discussions](https://github.com/your-username/autonomous_research/discussions)
- **Documentation**: Check the `docs/` directory for detailed guides

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **MITRE ATT&CK Framework** for cybersecurity technique definitions
- **Elasticsearch** for vector database capabilities
- **Ollama** for local LLM inference
- **OpenAI** for advanced language model integration
- The open-source security research community

## 📊 Project Stats

- **Languages**: Python, Shell, YAML
- **Test Coverage**: 95%+
- **Code Quality**: A+ (automated analysis)
- **Dependencies**: Regularly updated and security-scanned
- **Documentation**: Comprehensive API and user guides

