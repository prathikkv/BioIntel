#!/bin/bash

# Setup Vercel Environment Variables for BioIntel.AI Production
echo "🚀 Setting up Vercel environment variables for production..."

# Core database and security
echo "📊 Setting up core environment variables..."
echo "postgresql://postgres:coolHa!r50@db.fqrrmtqeqskqsxbewtfr.supabase.co:5432/postgres" | vercel env add DATABASE_URL production
echo "rediss://default:AVUKAAIjcDExYmI1MmZjM2M1NjA0OTNmYThjYmI1Y2M5MDQ4MjIzNnAxMA@upright-troll-21770.upstash.io:6379" | vercel env add REDIS_URL production
echo "mIpVuVarol0MO_F7KWv3KF_vE7Vf1sgYcNjbjd0bC9A" | vercel env add SECRET_KEY production
echo "61ectkbHQmy-8FZGo3z_VRtRMAbYbMqbmUOro98H0Zo" | vercel env add JWT_SECRET_KEY production

# CORS configuration
echo "🌐 Setting up CORS configuration..."
echo '["https://biointel.ai", "https://www.biointel.ai"]' | vercel env add CORS_ORIGINS production

# Other important environment variables
echo "⚙️ Setting up additional configuration..."
echo "production" | vercel env add ENVIRONMENT production
echo "False" | vercel env add DEBUG production
echo "INFO" | vercel env add LOG_LEVEL production

echo "✅ All environment variables set up successfully!"
echo ""
echo "🔄 Next steps:"
echo "1. Run: vercel --prod"
echo "2. Test the deployment"
echo "3. Check health endpoint"