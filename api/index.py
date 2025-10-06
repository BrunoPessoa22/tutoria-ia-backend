"""
Vercel serverless function entry point for FastAPI backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import our main app
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app as application

# Export for Vercel
app = application