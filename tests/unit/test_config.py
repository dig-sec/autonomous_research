
import pytest
from autonomous_research.config.secure_config import load_env_vars, load_config
from dotenv import load_dotenv
import os

def test_load_env_vars():
    # Load .env file before running the test
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))
    env = load_env_vars()
    assert isinstance(env, dict)
    assert 'OLLAMA_HOST' in env or 'ES_HOST' in env

def test_load_config():
    config = load_config()
    assert isinstance(config, dict)
    assert 'elasticsearch' in config or 'llm' in config
