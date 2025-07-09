#!/usr/bin/env python3
"""
Production Database Setup Script
Run this to initialize the production database with proper tables
"""

import os
import asyncio
from sqlalchemy import create_engine, text
from models.database import Base, engine
from models.user import User
from models.bioinformatics import Dataset, AnalysisJob, AnalysisResult, ExpressionData, GeneAnnotation
from models.literature import LiteratureSummary, ChatSession, ChatMessage, KnowledgeBase
from models.enterprise import Team, TeamMember, Workspace, SharedAnalysis, APIKey, UsageLog
# Report model might be in literature.py
from utils.logging import setup_logging
from utils.config import get_settings

async def create_tables():
    """Create all database tables"""
    print("🗄️  Creating database tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection test passed!")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise

async def setup_production_database():
    """Main setup function"""
    print("🚀 Setting up production database...")
    
    # Setup logging
    setup_logging()
    
    # Get settings
    settings = get_settings()
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🗄️  Database URL: {settings.DATABASE_URL[:50]}...")
    
    # Create tables
    await create_tables()
    
    print("🎉 Production database setup complete!")
    print("\nNext steps:")
    print("1. Update environment variables in Vercel")
    print("2. Run: vercel --prod")
    print("3. Test all endpoints")

if __name__ == "__main__":
    asyncio.run(setup_production_database())