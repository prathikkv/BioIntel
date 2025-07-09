#!/bin/bash

echo "🚀 BioIntel.AI Production Deployment Script"
echo "==========================================="

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Check if user is logged in
echo "🔐 Checking Vercel authentication..."
if ! vercel whoami &> /dev/null; then
    echo "⚠️  Not logged in to Vercel. Please run: vercel login"
    echo "After logging in, run this script again."
    exit 1
fi

echo "✅ Vercel authentication confirmed"

# Set up environment variables
echo "⚙️  Setting up environment variables..."
if [ -f "setup_vercel_env.sh" ]; then
    echo "🔑 Running environment setup script..."
    chmod +x setup_vercel_env.sh
    ./setup_vercel_env.sh
else
    echo "⚠️  Manual environment setup required:"
    echo "Run the following commands:"
    echo 'echo "postgresql://postgres:coolHa!r50@db.fqrrmtqeqskqsxbewtfr.supabase.co:5432/postgres" | vercel env add DATABASE_URL production'
    echo 'echo "rediss://default:AVUKAAIjcDExYmI1MmZjM2M1NjA0OTNmYThjYmI1Y2M5MDQ4MjIzNnAxMA@upright-troll-21770.upstash.io:6379" | vercel env add REDIS_URL production'
    echo 'echo "mIpVuVarol0MO_F7KWv3KF_vE7Vf1sgYcNjbjd0bC9A" | vercel env add SECRET_KEY production'
    echo 'echo "61ectkbHQmy-8FZGo3z_VRtRMAbYbMqbmUOro98H0Zo" | vercel env add JWT_SECRET_KEY production'
    echo ""
    echo "Press Enter after setting up environment variables..."
    read
fi

# Deploy to Vercel
echo "🌐 Deploying to Vercel..."
vercel --prod --yes

# Check deployment status
if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    echo ""
    echo "🔗 Your app is now live!"
    echo "📊 Health check: Visit your-app-url/health"
    echo "📖 API docs: Visit your-app-url/docs"
    echo ""
    echo "🧪 Test the deployment with:"
    echo "curl https://your-app-url/health"
else
    echo "❌ Deployment failed. Check the logs above for errors."
    echo ""
    echo "🔍 Common issues:"
    echo "1. Environment variables not set properly"
    echo "2. Database connection issues"
    echo "3. Package size exceeds limits"
    echo ""
    echo "🛠️  Debug with: vercel logs your-app-url"
fi