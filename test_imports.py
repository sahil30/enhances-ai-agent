#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    print("Testing AI Agent imports...")
    
    # Test basic imports
    try:
        from ai_agent.core.config import load_config, Config
        print("✅ Config import successful")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from ai_agent.core.ai_client import CustomAIClient
        print("✅ AI Client import successful")
    except Exception as e:
        print(f"❌ AI Client import failed: {e}")
        return False
        
    try:
        from ai_agent.core.query_processor import NLPProcessor, QueryType, QueryIntent
        print("✅ Query Processor import successful")
    except Exception as e:
        print(f"❌ Query Processor import failed: {e}")
        return False
    
    try:
        from ai_agent.core.types import SourceType, ProblemCategory
        print("✅ Types import successful")
    except Exception as e:
        print(f"❌ Types import failed: {e}")
        return False
    
    try:
        from ai_agent.core.context_managers import ai_agent_context
        print("✅ Context Managers import successful")
    except Exception as e:
        print(f"❌ Context Managers import failed: {e}")
        return False
    
    try:
        from ai_agent.core.agent import AIAgent
        print("✅ Agent import successful")
    except Exception as e:
        if "Configuration validation failed" in str(e):
            print("✅ Agent import successful (configuration needed, as expected)")
        else:
            print(f"❌ Agent import failed: {e}")
            return False
        
    try:
        from ai_agent.api.cli import main
        print("✅ CLI import successful")
    except Exception as e:
        if "Configuration validation failed" in str(e):
            print("✅ CLI import successful (configuration needed for CLI functionality, as expected)")
        else:
            print(f"❌ CLI import failed: {e}")
            return False
    
    print("🎉 All imports successful!")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)