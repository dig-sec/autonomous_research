#!/bin/bash
# Setup script for Autonomous Research System
# Sets up environment variables and configuration

echo "🔧 Setting up Autonomous Research System..."

# Check if .env file exists
if [ -f ".env" ]; then
    echo "✅ .env file found"
    source .env
else
    echo "⚠️  .env file not found. Creating from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📝 Created .env from template. Please edit .env with your actual values:"
        echo "   - ES_PASSWORD: Your Elasticsearch password (set in .env or environment)"
        echo "   - GITHUB_TOKEN: Your GitHub API token (optional)"
        echo ""
        echo "Then run: source .env"
    else
        echo "❌ .env.example not found. Please create .env manually."
        exit 1
    fi
fi

# Check if ES_PASSWORD is set
if [ -z "$ES_PASSWORD" ]; then
    echo "⚠️  ES_PASSWORD environment variable not set"
    echo "Please set it with: export ES_PASSWORD=your_elasticsearch_password"
    echo "Or add it to your .env file"
else
    echo "✅ ES_PASSWORD is configured"
fi

# Check Elasticsearch connection
echo "🔍 Testing Elasticsearch connection..."
if command -v curl >/dev/null 2>&1; then
    if [ -n "$ES_PASSWORD" ]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -u "elastic:$ES_PASSWORD" "http://localhost:9200/")
        if [ "$HTTP_CODE" = "200" ]; then
            echo "✅ Elasticsearch connection successful"
        else
            echo "❌ Elasticsearch connection failed (HTTP $HTTP_CODE)"
            echo "Please check your ES_PASSWORD and ensure Elasticsearch is running"
        fi
    else
        echo "⚠️  Cannot test connection without ES_PASSWORD"
    fi
else
    echo "⚠️  curl not found, skipping connection test"
fi

echo ""
echo "🚀 Setup complete! You can now run:"
echo "   PYTHONPATH=src python3 run_autonomous.py"
echo ""
echo "🔒 Security: Passwords are now loaded from environment variables"
echo "   Make sure to never commit .env files to git!"
