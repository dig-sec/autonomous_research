#!/usr/bin/env python3
"""
System Status Check

Quick health check for the autonomous research system.
"""
import os
import sys
import json
import subprocess
from pathlib import Path

def load_env_vars():
    """Load environment variables from .env file."""
    env_vars = {}
    if Path(".env").exists():
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

def check_environment():
    """Check environment setup."""
    print("🔧 Environment Check:")
    
    # Check .env file
    if Path(".env").exists():
        print("  ✅ .env file found")
        
        # Load .env file
        env_vars = {}
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
        
        # Check required variables
        required_vars = ["ES_PASSWORD", "ES_HOST", "ES_PORT", "ES_USER"]
        missing = []
        for var in required_vars:
            if var not in env_vars or not env_vars[var]:
                missing.append(var)
        
        if missing:
            print(f"  ⚠️  Missing environment variables: {', '.join(missing)}")
        else:
            print("  ✅ All required environment variables found")
            
        return len(missing) == 0
    else:
        print("  ❌ .env file not found")
        return False

def check_queue():
    """Check research queue status."""
    print("\n📊 Queue Status:")
    
    if Path("research_queue.json").exists():
        with open("research_queue.json") as f:
            queue = json.load(f)
        
        techniques = len(queue.get("techniques", []))
        cves = len(queue.get("cves", []))
        
        print(f"  ✅ Queue file found")
        print(f"  📈 {techniques} techniques, {cves} CVEs")
        
        if techniques > 0:
            print("  ✅ Queue populated")
        else:
            print("  ⚠️  Queue empty - run populate command")
            
    else:
        print("  ❌ No queue file found - run populate command")

def check_elasticsearch():
    """Check Elasticsearch connection."""
    print("\n🔍 Elasticsearch Check:")
    
    env_vars = load_env_vars()
    host = env_vars.get("ES_HOST", "localhost")
    port = env_vars.get("ES_PORT", "9200")
    user = env_vars.get("ES_USER", "elastic")
    password = env_vars.get("ES_PASSWORD", "")
    
    if not password:
        print("  ❌ ES_PASSWORD not set")
        return False
    
    try:
        result = subprocess.run([
            "curl", "-s", "-u", f"{user}:{password}", 
            f"http://{host}:{port}/"
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print("  ✅ Elasticsearch connection successful")
            return True
        else:
            print(f"  ❌ Elasticsearch connection failed (exit code {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print("  ❌ Elasticsearch connection timeout")
        return False
    except FileNotFoundError:
        print("  ⚠️  curl not found, skipping connection test")
        return None

def check_dependencies():
    """Check Python dependencies."""
    print("\n📦 Dependencies Check:")
    
    required_packages = [
        "elasticsearch",
        "sentence_transformers", 
        "requests",
        "yaml"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n  Install missing packages:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True

def main():
    """Run all status checks."""
    print("🚀 Autonomous Research System Status")
    print("=" * 50)
    
    checks = [
        check_environment(),
        check_dependencies(), 
        check_queue(),
        check_elasticsearch()
    ]
    
    # Filter out None results
    checks = [c for c in checks if c is not None]
    
    print("\n" + "=" * 50)
    
    if all(checks):
        print("🎉 All systems operational!")
        print("\nNext steps:")
        print("  ./quickstart.py           # Interactive interface") 
        print("  python3 research_manager.py populate  # Populate queue")
        print("  python3 research_manager.py build --max-items 5  # Build KB")
        return 0
    else:
        failed = len([c for c in checks if not c])
        print(f"⚠️  {failed} issues found - see above for details")
        print("\nSetup steps:")
        print("  ./setup.sh               # Environment setup")
        print("  pip install -r requirements.txt  # Install dependencies")
        return 1

if __name__ == "__main__":
    # Load environment if available
    if Path(".env").exists():
        import subprocess
        subprocess.run(["bash", "-c", "source .env && env"], capture_output=True)
    
    sys.exit(main())
