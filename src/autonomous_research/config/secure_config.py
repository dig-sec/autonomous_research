"""
Secure Configuration Loader

Loads configuration from YAML files and environment variables.
Environment variables take precedence over config file values.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def load_env_vars() -> Dict[str, str]:
    """Load environment variables with ES_ prefix."""
    env_vars = {}
    for key, value in os.environ.items():
        if key.startswith(('ES_', 'OLLAMA_', 'GITHUB_', 'RATE_LIMIT_')):
            env_vars[key] = value
    return env_vars

def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file and override with environment variables.
    
    Environment variable mapping:
    ES_HOST -> elasticsearch.host
    ES_PORT -> elasticsearch.port  
    ES_USER -> elasticsearch.user
    ES_PASSWORD -> elasticsearch.password
    OLLAMA_HOST -> llm.ollama_host
    GITHUB_TOKEN -> github.token
    """
    config = {}
    config_file = Path(config_path)
    if not config_file.exists():
        # Try src/autonomous_research/config/config.yaml
        alt_path = Path(__file__).parent / "config.yaml"
        if alt_path.exists():
            config_file = alt_path
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
            logger.info(f"Loaded base config from {config_file}")
        except Exception as e:
            logger.warning(f"Could not load config file {config_path}: {e}")
    
    # Override with environment variables
    env_vars = load_env_vars()
    
    if env_vars:
        logger.info(f"Found {len(env_vars)} environment variables for config override")
        
        # Elasticsearch overrides
        if 'ES_HOST' in env_vars:
            config.setdefault('elasticsearch', {})['host'] = env_vars['ES_HOST']
        if 'ES_PORT' in env_vars:
            config.setdefault('elasticsearch', {})['port'] = int(env_vars['ES_PORT'])
        if 'ES_USER' in env_vars:
            config.setdefault('elasticsearch', {})['user'] = env_vars['ES_USER']
        if 'ES_PASSWORD' in env_vars:
            config.setdefault('elasticsearch', {})['password'] = env_vars['ES_PASSWORD']
            
        # LLM overrides
        if 'OLLAMA_HOST' in env_vars:
            config.setdefault('llm', {})['ollama_host'] = env_vars['OLLAMA_HOST']
            
        # GitHub overrides
        if 'GITHUB_TOKEN' in env_vars:
            config.setdefault('github', {})['token'] = env_vars['GITHUB_TOKEN']
            
        # Rate limiting overrides
        if 'RATE_LIMIT_GITHUB' in env_vars:
            config.setdefault('rate_limits', {})['github_api'] = float(env_vars['RATE_LIMIT_GITHUB'])
        if 'RATE_LIMIT_MITRE' in env_vars:
            config.setdefault('rate_limits', {})['mitre_api'] = float(env_vars['RATE_LIMIT_MITRE'])
        if 'RATE_LIMIT_WEB' in env_vars:
            config.setdefault('rate_limits', {})['general_web'] = float(env_vars['RATE_LIMIT_WEB'])
    
    return config

def get_elasticsearch_config() -> Dict[str, Any]:
    """Get Elasticsearch configuration with environment variable overrides."""
    config = load_config()
    es_config = config.get('elasticsearch', {})
    
    # Provide secure defaults if no config found
    return {
        'host': es_config.get('host', 'localhost'),
        'port': es_config.get('port', 9200),
        'user': es_config.get('user', 'elastic'),
        'password': es_config.get('password', os.getenv('ES_PASSWORD', '')),
        'output_index': es_config.get('output_index', 'autonomous_research_outputs')
    }

def get_llm_config() -> Dict[str, Any]:
    """Get LLM configuration with environment variable overrides."""
    config = load_config()
    return config.get('llm', {
        'default_model': 'llama2-uncensored:7b',
        'ollama_host': os.getenv('OLLAMA_HOST', 'http://localhost:11434'),
        'temperature': 0.7,
        'max_tokens': 2000,
        'timeout': 120
    })
