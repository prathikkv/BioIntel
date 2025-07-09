#!/usr/bin/env python3
"""
Generate Production Secrets for BioIntel.AI
Run this to generate secure secrets for production deployment
"""

import secrets
import string
import base64
import os
from cryptography.fernet import Fernet

def generate_secret_key(length=64):
    """Generate a secure secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_jwt_secret(length=32):
    """Generate a JWT secret key"""
    return base64.urlsafe_b64encode(os.urandom(length)).decode()

def generate_fernet_key():
    """Generate a Fernet encryption key"""
    return Fernet.generate_key().decode()

def main():
    print("🔐 Generating production secrets for BioIntel.AI...")
    print("=" * 60)
    
    # Generate secrets
    secret_key = generate_secret_key()
    jwt_secret = generate_jwt_secret()
    fernet_key = generate_fernet_key()
    
    print("\n🔑 Generated Secrets:")
    print(f"SECRET_KEY={secret_key}")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print(f"FERNET_KEY={fernet_key}")
    
    print("\n📋 Vercel Environment Variables:")
    print("Run these commands to set up your Vercel environment:")
    print(f'vercel env add SECRET_KEY production <<< "{secret_key}"')
    print(f'vercel env add JWT_SECRET_KEY production <<< "{jwt_secret}"')
    print(f'vercel env add FERNET_KEY production <<< "{fernet_key}"')
    
    print("\n⚠️  IMPORTANT:")
    print("1. Save these secrets securely - they cannot be recovered!")
    print("2. Never commit these to version control")
    print("3. Use different secrets for different environments")
    
    # Save to a secure file
    with open(".secrets.production", "w") as f:
        f.write(f"SECRET_KEY={secret_key}\n")
        f.write(f"JWT_SECRET_KEY={jwt_secret}\n")
        f.write(f"FERNET_KEY={fernet_key}\n")
    
    print("\n✅ Secrets saved to .secrets.production (add to .gitignore)")

if __name__ == "__main__":
    main()