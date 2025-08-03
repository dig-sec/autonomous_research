#!/usr/bin/env python3
"""
Quick Start Script for Autonomous Research

Simple entry point to get started quickly.
"""
import subprocess
import sys
import os

def main():
    print("🚀 Autonomous Research Quick Start")
    print("=" * 50)
    
    # Check environment
    if not os.path.exists('.env'):
        print("⚠️  No .env file found. Run: ./setup.sh")
        return 1
    
    # Load environment
    print("📋 Available commands:")
    print("  1. populate  - Populate research queue from all sources")
    print("  2. stats     - Show queue statistics")
    print("  3. build     - Build knowledge base from queue (limited)")
    print("  4. autonomous - Run in autonomous mode")
    print("  5. clear     - Clear the research queue")
    print()
    
    choice = input("Enter choice (1-5) or command name: ").strip()
    
    command_map = {
        "1": "populate",
        "2": "stats", 
        "3": "build",
        "4": "autonomous",
        "5": "clear",
        "populate": "populate",
        "stats": "stats",
        "build": "build", 
        "autonomous": "autonomous",
        "clear": "clear"
    }
    
    command = command_map.get(choice)
    if not command:
        print("❌ Invalid choice")
        return 1
    
    # Special handling for build command
    if command == "build":
        limit = input("Max items to process (default 5, enter for default): ").strip()
        if limit and limit.isdigit():
            cmd = ["python3", "cli/research_manager.py", "build", "--max-items", limit]
        else:
            cmd = ["python3", "cli/research_manager.py", "build", "--max-items", "5"]
    else:
        cmd = ["python3", "cli/research_manager.py", command]
    
    # Set environment and run
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    
    print(f"🔄 Running: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, env=env)
        return result.returncode
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
