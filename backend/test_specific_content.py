#!/usr/bin/env python3
"""
Test with very specific content that Claude couldn't know from training.
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import config
from rag_system import RAGSystem


def test_specific_content_queries():
    """Test with queries that require searching actual course content"""
    print("Testing with specific content queries...")

    rag = RAGSystem(config)

    # Let's first see what content is actually in the database
    print("=== Checking actual database content ===")
    results = rag.vector_store.search("", limit=1)  # Get any content
    if results.documents:
        print(f"Sample content from database: {results.documents[0][:200]}...")
        print(f"Metadata: {results.metadata[0] if results.metadata else 'None'}")

    # Test with very specific queries that would need the actual content
    specific_queries = [
        "What specific example is given in lesson 1 of the MCP course?",
        "What exact code snippet is shown in lesson 3?",
        "What are the exact steps mentioned in lesson 2 of the Computer Use course?",
        "Quote a specific sentence from lesson 5 of any course",
        "What is the instructor's exact wording about prompt caching?",
    ]

    for i, query in enumerate(specific_queries, 1):
        print(f"\n{'-'*60}")
        print(f"Specific Test {i}: {query}")
        print("-" * 60)

        try:
            # Reset sources
            rag.tool_manager.reset_sources()

            # Execute query with explicit instructions
            enhanced_query = f"""You MUST search the course content to answer this question. Do not use your general knowledge. Search for: {query}"""

            response, sources, source_links = rag.query(enhanced_query)

            print(f"Response length: {len(response)}")
            print(f"Sources count: {len(sources)}")
            print(f"Response: {response}")

            if sources:
                print(f"✅ Sources used: {sources}")
            else:
                print("❌ No sources - Claude still didn't use tools")

        except Exception as e:
            print(f"❌ Query failed: {str(e)}")


def test_force_tool_usage():
    """Try to force tool usage with very explicit instructions"""
    print("\n" + "=" * 60)
    print("Testing with FORCED tool usage instructions...")
    print("=" * 60)

    rag = RAGSystem(config)

    # Very explicit query
    forced_query = """You are required to use the search_course_content tool to find information about machine learning concepts in the course database. Please search for "machine learning" and provide the results."""

    try:
        rag.tool_manager.reset_sources()
        response, sources, source_links = rag.query(forced_query)

        print(f"Response: {response}")
        print(f"Sources: {sources}")

        if sources:
            print("✅ Forced tool usage worked")
        else:
            print("❌ Even forced instructions didn't work")

    except Exception as e:
        print(f"❌ Forced query failed: {str(e)}")


def examine_api_behavior():
    """Check the actual API calls being made"""
    print("\n" + "=" * 60)
    print("Examining API behavior...")
    print("=" * 60)

    # Let's monkey patch the API call to see what's happening
    import anthropic
    from ai_generator import AIGenerator

    original_create = None

    def patched_create(*args, **kwargs):
        print("API Call Parameters:")
        print(f"  Model: {kwargs.get('model', 'not specified')}")
        print(f"  Tools provided: {'tools' in kwargs}")
        if "tools" in kwargs:
            print(f"  Number of tools: {len(kwargs['tools'])}")
            print(f"  Tool names: {[t['name'] for t in kwargs['tools']]}")
        print(f"  Tool choice: {kwargs.get('tool_choice', 'not specified')}")
        print(
            f"  Query: {kwargs.get('messages', [{}])[0].get('content', 'not found')[:100]}..."
        )

        # Call original
        result = original_create(*args, **kwargs)

        print(f"API Response:")
        print(f"  Stop reason: {result.stop_reason}")
        print(f"  Content blocks: {len(result.content)}")
        for i, block in enumerate(result.content):
            print(f"    Block {i}: type={getattr(block, 'type', 'unknown')}")

        return result

    # Patch the method
    rag = RAGSystem(config)
    original_create = rag.ai_generator.client.messages.create
    rag.ai_generator.client.messages.create = patched_create

    try:
        print("Making API call with patched method...")
        response, sources, source_links = rag.query("What is in the MCP course?")
        print(f"Final sources: {sources}")
    except Exception as e:
        print(f"Patched call failed: {str(e)}")
    finally:
        # Restore original method
        if original_create:
            rag.ai_generator.client.messages.create = original_create


def main():
    test_specific_content_queries()
    test_force_tool_usage()
    examine_api_behavior()


if __name__ == "__main__":
    main()
