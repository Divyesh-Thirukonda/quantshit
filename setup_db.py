"""
Database setup script.
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from api.database import DATABASE_SCHEMA


def print_schema():
    """Print the database schema that needs to be run in Supabase."""
    print("📁 Database Schema Setup")
    print("="*50)
    print("Copy and run the following SQL in your Supabase SQL editor:")
    print()
    print(DATABASE_SCHEMA)
    print()
    print("="*50)
    print("✅ After running this schema, your database will be ready!")


if __name__ == "__main__":
    print_schema()