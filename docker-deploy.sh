#!/bin/bash

# BioIntel.AI Docker Deployment Script

echo "🐳 BioIntel.AI Docker Deployment"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "info") echo -e "${BLUE}ℹ️  $message${NC}" ;;
        "success") echo -e "${GREEN}✅ $message${NC}" ;;
        "warning") echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "error") echo -e "${RED}❌ $message${NC}" ;;
    esac
}

# Default values
ENVIRONMENT="development"
REBUILD=false
DETACH=true
SCALE_API=1
SCALE_FRONTEND=1

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --rebuild)
            REBUILD=true
            shift
            ;;
        --foreground)
            DETACH=false
            shift
            ;;
        --scale-api)
            SCALE_API="$2"
            shift 2
            ;;
        --scale-frontend)
            SCALE_FRONTEND="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -e, --environment ENV    Environment (development, production)"
            echo "  --rebuild               Rebuild Docker images"
            echo "  --foreground            Run in foreground (no detach)"
            echo "  --scale-api N           Scale API service to N instances"
            echo "  --scale-frontend N      Scale frontend service to N instances"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            print_status "error" "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_status "info" "Deploying BioIntel.AI with Docker Compose"
print_status "info" "Environment: $ENVIRONMENT"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_status "error" "Docker not found. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_status "error" "Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_status "error" "docker-compose.yml not found. Please run this script from the project root."
    exit 1
fi

# Create necessary directories
print_status "info" "Creating necessary directories..."
mkdir -p logs uploads reports static ssl

# Set environment variables
export ENVIRONMENT=$ENVIRONMENT
export COMPOSE_PROJECT_NAME="biointel-ai"

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    print_status "info" "Loading environment variables from .env file..."
    set -a
    source .env
    set +a
else
    print_status "warning" "No .env file found. Using default values."
    print_status "info" "Creating sample .env file..."
    cat > .env << EOF
# BioIntel.AI Environment Variables
ENVIRONMENT=$ENVIRONMENT
DEBUG=False
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
DATABASE_URL=postgresql://biointel:biointel@db:5432/biointel_db
REDIS_URL=redis://redis:6379/0
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
SENTRY_DSN=your-sentry-dsn
EOF
    print_status "warning" "Please update the .env file with your actual values before running again."
fi

# Stop existing containers
print_status "info" "Stopping existing containers..."
docker-compose down

# Build/rebuild images if requested
if [ "$REBUILD" = true ]; then
    print_status "info" "Rebuilding Docker images..."
    docker-compose build --no-cache
else
    print_status "info" "Building Docker images..."
    docker-compose build
fi

# Check if build was successful
if [ $? -ne 0 ]; then
    print_status "error" "Docker build failed!"
    exit 1
fi

# Start services
print_status "info" "Starting services..."

COMPOSE_CMD="docker-compose up"

if [ "$DETACH" = true ]; then
    COMPOSE_CMD="$COMPOSE_CMD -d"
fi

# Scale services if requested
if [ "$SCALE_API" -gt 1 ] || [ "$SCALE_FRONTEND" -gt 1 ]; then
    print_status "info" "Scaling services: API=$SCALE_API, Frontend=$SCALE_FRONTEND"
    $COMPOSE_CMD --scale api=$SCALE_API --scale frontend=$SCALE_FRONTEND
else
    $COMPOSE_CMD
fi

# Check if services started successfully
if [ $? -ne 0 ]; then
    print_status "error" "Failed to start services!"
    exit 1
fi

print_status "success" "Services started successfully!"

# Wait for services to be ready
print_status "info" "Waiting for services to be ready..."
sleep 15

# Health checks
print_status "info" "Performing health checks..."

# Check API health
API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
if [ "$API_HEALTH" = "200" ]; then
    print_status "success" "API is healthy"
else
    print_status "warning" "API health check failed (HTTP $API_HEALTH)"
fi

# Check frontend health
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/_stcore/health || echo "000")
if [ "$FRONTEND_HEALTH" = "200" ]; then
    print_status "success" "Frontend is healthy"
else
    print_status "warning" "Frontend health check failed (HTTP $FRONTEND_HEALTH)"
fi

# Check database connection
DB_STATUS=$(docker-compose exec -T db pg_isready -h localhost -p 5432 || echo "failed")
if [[ "$DB_STATUS" == *"accepting connections"* ]]; then
    print_status "success" "Database is ready"
else
    print_status "warning" "Database connection check failed"
fi

# Check Redis connection
REDIS_STATUS=$(docker-compose exec -T redis redis-cli ping || echo "failed")
if [ "$REDIS_STATUS" = "PONG" ]; then
    print_status "success" "Redis is ready"
else
    print_status "warning" "Redis connection check failed"
fi

# Show running services
print_status "info" "Running services:"
docker-compose ps

# Show logs if not running in detached mode
if [ "$DETACH" = false ]; then
    print_status "info" "Showing logs (Ctrl+C to exit)..."
    docker-compose logs -f
fi

# Summary
echo ""
echo "🎉 Deployment Summary"
echo "===================="
echo "Environment: $ENVIRONMENT"
echo "API URL: http://localhost:8000"
echo "Frontend URL: http://localhost:8501"
echo "Nginx URL: http://localhost:80"
echo "Database: localhost:5432"
echo "Redis: localhost:6379"
echo ""

# Show useful commands
echo "📋 Useful Commands:"
echo "- View logs: docker-compose logs -f"
echo "- Stop services: docker-compose down"
echo "- Restart services: docker-compose restart"
echo "- Scale services: docker-compose up --scale api=3"
echo "- Enter container: docker-compose exec api bash"
echo "- View service status: docker-compose ps"
echo ""

print_status "success" "BioIntel.AI deployment completed!"

# Create deployment info
cat > deployment-info.json << EOF
{
  "deployment_type": "docker-compose",
  "environment": "$ENVIRONMENT",
  "deployment_time": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "api_url": "http://localhost:8000",
  "frontend_url": "http://localhost:8501",
  "nginx_url": "http://localhost:80",
  "git_commit": "$(git rev-parse HEAD || echo 'unknown')",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD || echo 'unknown')",
  "services": {
    "api": {
      "instances": $SCALE_API,
      "health_check": "$API_HEALTH"
    },
    "frontend": {
      "instances": $SCALE_FRONTEND,
      "health_check": "$FRONTEND_HEALTH"
    },
    "database": {
      "status": "$DB_STATUS"
    },
    "redis": {
      "status": "$REDIS_STATUS"
    }
  }
}
EOF

print_status "info" "Deployment information saved to deployment-info.json"
print_status "info" "Happy coding! 🚀"