# Quick deployment script for production
#!/bin/bash

set -e

echo "🚀 Qoneqt Agent Network - Quick Deploy"
echo "======================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo "⚠️  IMPORTANT: Edit .env and set:"
    echo "   - DB_PASSWORD (strong password)"
    echo "   - SECRET_KEY (run: openssl rand -hex 32)"
    echo ""
    read -p "Press enter to continue after editing .env..."
fi

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not found!"
    echo "Install with: curl -fsSL https://ollama.com/install.sh | sh"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Ollama found"
    
    # Check if Ollama is running
    if ! pgrep -x "ollama" > /dev/null; then
        echo "🔄 Starting Ollama..."
        ollama serve &
        sleep 3
    fi
    
    # Pull model if not exists
    MODEL="${OLLAMA_MODEL:-qwen2.5:7b}"
    if ! ollama list | grep -q "$MODEL"; then
        echo "📥 Pulling model: $MODEL"
        ollama pull "$MODEL"
    fi
fi

# Build and start containers
echo ""
echo "🔨 Building Docker images..."
docker compose build

echo ""
echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Access your application:"
echo "   Web UI:    http://localhost:3000"
echo "   API Docs:  http://localhost:8080/docs"
echo "   Database:  http://localhost:8081"
echo "   Grafana:   http://localhost:3001"
echo ""
echo "📝 View logs with: docker compose logs -f"
echo "🛑 Stop with: docker compose down"
