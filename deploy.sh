#!/bin/bash

# BioIntel.AI Deployment Script
# This script handles deployment to Vercel and other platforms

echo "🚀 BioIntel.AI Deployment Script"
echo "================================"

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
PLATFORM="vercel"
ENVIRONMENT="production"
SKIP_TESTS=false
SKIP_BUILD=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -p, --platform PLATFORM     Deployment platform (vercel, heroku, docker)"
            echo "  -e, --environment ENV        Environment (production, staging)"
            echo "  --skip-tests                 Skip running tests"
            echo "  --skip-build                 Skip build steps"
            echo "  -h, --help                   Show this help message"
            exit 0
            ;;
        *)
            print_status "error" "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_status "info" "Deploying to $PLATFORM in $ENVIRONMENT environment"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    print_status "error" "requirements.txt not found. Please run this script from the project root."
    exit 1
fi

# Pre-deployment checks
print_status "info" "Running pre-deployment checks..."

# Check if required tools are installed
if [ "$PLATFORM" = "vercel" ]; then
    if ! command -v vercel &> /dev/null; then
        print_status "error" "Vercel CLI not found. Installing..."
        npm install -g vercel
    fi
elif [ "$PLATFORM" = "heroku" ]; then
    if ! command -v heroku &> /dev/null; then
        print_status "error" "Heroku CLI not found. Please install it first."
        exit 1
    fi
elif [ "$PLATFORM" = "docker" ]; then
    if ! command -v docker &> /dev/null; then
        print_status "error" "Docker not found. Please install it first."
        exit 1
    fi
fi

# Run tests if not skipped
if [ "$SKIP_TESTS" = false ]; then
    print_status "info" "Running tests..."
    ./run_tests.sh -t all
    if [ $? -ne 0 ]; then
        print_status "error" "Tests failed. Deployment aborted."
        exit 1
    fi
    print_status "success" "All tests passed!"
fi

# Build steps if not skipped
if [ "$SKIP_BUILD" = false ]; then
    print_status "info" "Running build steps..."
    
    # Install dependencies
    pip install -r requirements.txt
    
    # Run any build commands
    if [ -f "build.py" ]; then
        python build.py
    fi
    
    print_status "success" "Build completed!"
fi

# Environment-specific configurations
case $ENVIRONMENT in
    "production")
        print_status "info" "Setting up production environment..."
        export DEBUG=False
        export ENVIRONMENT=production
        ;;
    "staging")
        print_status "info" "Setting up staging environment..."
        export DEBUG=False
        export ENVIRONMENT=staging
        ;;
    *)
        print_status "error" "Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

# Platform-specific deployment
case $PLATFORM in
    "vercel")
        print_status "info" "Deploying to Vercel..."
        
        # Check if logged in
        if ! vercel whoami &> /dev/null; then
            print_status "info" "Please login to Vercel:"
            vercel login
        fi
        
        # Set environment variables
        print_status "info" "Setting up environment variables..."
        
        # Check if .env file exists
        if [ -f ".env" ]; then
            print_status "warning" "Found .env file. Make sure to set these variables in Vercel:"
            echo "Required environment variables:"
            echo "- DATABASE_URL"
            echo "- SECRET_KEY"
            echo "- JWT_SECRET_KEY"
            echo "- ANTHROPIC_API_KEY"
            echo "- OPENAI_API_KEY"
            echo "- REDIS_URL"
            echo ""
            echo "Set them using: vercel env add <NAME>"
        fi
        
        # Deploy
        if [ "$ENVIRONMENT" = "production" ]; then
            vercel --prod
        else
            vercel
        fi
        
        if [ $? -eq 0 ]; then
            print_status "success" "Deployment to Vercel completed!"
            
            # Get deployment URL
            DEPLOYMENT_URL=$(vercel ls | grep "biointel-ai-backend" | head -1 | awk '{print $2}')
            if [ -n "$DEPLOYMENT_URL" ]; then
                print_status "success" "Deployment URL: https://$DEPLOYMENT_URL"
            fi
        else
            print_status "error" "Deployment to Vercel failed!"
            exit 1
        fi
        ;;
        
    "heroku")
        print_status "info" "Deploying to Heroku..."
        
        # Check if logged in
        if ! heroku whoami &> /dev/null; then
            print_status "info" "Please login to Heroku:"
            heroku login
        fi
        
        # Create or update Procfile
        if [ ! -f "Procfile" ]; then
            echo "web: uvicorn api.main:app --host 0.0.0.0 --port \$PORT" > Procfile
            print_status "info" "Created Procfile"
        fi
        
        # Create or update runtime.txt
        if [ ! -f "runtime.txt" ]; then
            echo "python-3.9.18" > runtime.txt
            print_status "info" "Created runtime.txt"
        fi
        
        # Deploy
        git add .
        git commit -m "Deploy to Heroku" || true
        git push heroku main
        
        if [ $? -eq 0 ]; then
            print_status "success" "Deployment to Heroku completed!"
            
            # Get deployment URL
            DEPLOYMENT_URL=$(heroku apps:info --json | jq -r '.app.web_url')
            if [ -n "$DEPLOYMENT_URL" ]; then
                print_status "success" "Deployment URL: $DEPLOYMENT_URL"
            fi
        else
            print_status "error" "Deployment to Heroku failed!"
            exit 1
        fi
        ;;
        
    "docker")
        print_status "info" "Building Docker image..."
        
        # Create Dockerfile if it doesn't exist
        if [ ! -f "Dockerfile" ]; then
            cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
            print_status "info" "Created Dockerfile"
        fi
        
        # Build image
        docker build -t biointel-ai .
        
        if [ $? -eq 0 ]; then
            print_status "success" "Docker image built successfully!"
            print_status "info" "To run the container: docker run -p 8000:8000 biointel-ai"
        else
            print_status "error" "Docker build failed!"
            exit 1
        fi
        ;;
        
    *)
        print_status "error" "Unknown platform: $PLATFORM"
        exit 1
        ;;
esac

# Post-deployment checks
print_status "info" "Running post-deployment checks..."

# Health check (if URL is available)
if [ -n "$DEPLOYMENT_URL" ]; then
    print_status "info" "Checking deployment health..."
    
    # Wait a bit for deployment to be ready
    sleep 10
    
    # Check health endpoint
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$DEPLOYMENT_URL/health" || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_status "success" "Deployment is healthy!"
    else
        print_status "warning" "Health check failed (HTTP $HTTP_CODE). Deployment may still be starting up."
    fi
fi

# Create deployment info file
cat > deployment-info.json << EOF
{
  "platform": "$PLATFORM",
  "environment": "$ENVIRONMENT",
  "deployment_time": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "deployment_url": "$DEPLOYMENT_URL",
  "git_commit": "$(git rev-parse HEAD || echo 'unknown')",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD || echo 'unknown')"
}
EOF

print_status "success" "Deployment information saved to deployment-info.json"

# Summary
echo ""
echo "🎉 Deployment Summary"
echo "===================="
echo "Platform: $PLATFORM"
echo "Environment: $ENVIRONMENT"
echo "Status: Success"
if [ -n "$DEPLOYMENT_URL" ]; then
    echo "URL: $DEPLOYMENT_URL"
fi
echo "Time: $(date)"
echo ""

print_status "success" "Deployment completed successfully!"

# Next steps
echo "📋 Next Steps:"
echo "1. Test the deployed application"
echo "2. Monitor logs for any issues"
echo "3. Update DNS if needed"
echo "4. Set up monitoring and alerts"
echo ""

print_status "info" "Happy deploying! 🚀"