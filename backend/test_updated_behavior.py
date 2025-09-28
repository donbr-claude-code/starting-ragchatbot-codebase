#!/usr/bin/env python3
"""
Test the updated system behavior
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import config
from rag_system import RAGSystem


def test_updated_behavior():
    """Test queries with the updated system prompt"""
    print("Testing updated system behavior...")

    rag = RAGSystem(config)

    test_queries = [
        ("Give me the outline of the Computer Use course", "Should use get_course_outline tool"),
        ("What does the MCP course cover?", "Should use get_course_outline or search tool"),
        ("What is machine learning?", "Should use search tool (course-related)"),
        ("What is 2+2?", "Should NOT use tools (pure math)"),
        ("Hello how are you?", "Should NOT use tools (greeting)"),
    ]

    for i, (query, expected) in enumerate(test_queries, 1):
        print(f"\n{'-'*60}")
        print(f"Test {i}: {query}")
        print(f"Expected: {expected}")
        print('-'*60)

        try:
            # Reset sources
            rag.tool_manager.reset_sources()

            # Execute query
            response, sources, source_links = rag.query(query)

            print(f"Response length: {len(response)}")
            print(f"Sources count: {len(sources)}")

            if sources:
                print(f"✅ Used tools - Sources: {sources[:2]}...")  # Show first 2 sources
                print(f"Response preview: {response[:150]}...")
            else:
                print("❌ No tools used")
                print(f"Response preview: {response[:150]}...")

        except Exception as e:
            print(f"❌ Query failed: {str(e)}")


if __name__ == "__main__":
    test_updated_behavior()