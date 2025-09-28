#!/usr/bin/env python3
"""
Test the current system prompt behavior
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from ai_generator import AIGenerator
from config import config


def test_current_prompt():
    """Test what the current system prompt contains"""
    generator = AIGenerator(config.ANTHROPIC_API_KEY, config.ANTHROPIC_MODEL)

    print("Current system prompt:")
    print("-" * 60)
    print(generator.SYSTEM_PROMPT)
    print("-" * 60)

    # Check for key phrases
    key_phrases = [
        "CRITICAL: You MUST use tools",
        "ALWAYS use tools for course-related queries",
        "Course-related questions",
    ]

    print("Key phrases check:")
    for phrase in key_phrases:
        if phrase in generator.SYSTEM_PROMPT:
            print(f"✅ Found: '{phrase}'")
        else:
            print(f"❌ Missing: '{phrase}'")


if __name__ == "__main__":
    test_current_prompt()
