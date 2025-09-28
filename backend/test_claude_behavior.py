#!/usr/bin/env python3
"""
Test script to specifically examine Claude's tool usage behavior.
"""

import sys
import os
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import config
from rag_system import RAGSystem
from ai_generator import AIGenerator
from search_tools import ToolManager, CourseSearchTool, CourseOutlineTool
from vector_store import VectorStore


def test_claude_tool_usage():
    """Test if Claude actually uses tools when prompted"""
    print("Testing Claude's tool usage behavior...")

    # Initialize components
    rag = RAGSystem(config)

    # Different types of queries to test
    test_queries = [
        "What is machine learning?",  # Should potentially use search
        "Tell me about the MCP course", # Should definitely use search
        "Give me the outline of the Computer Use course", # Should use outline tool
        "What are the main topics covered in these courses?", # Should use search
        "Hello, how are you?", # Should NOT use tools
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'-'*60}")
        print(f"Test {i}: {query}")
        print('-'*60)

        try:
            # Reset sources
            rag.tool_manager.reset_sources()

            # Execute query
            response, sources, source_links = rag.query(query)

            print(f"Response length: {len(response)}")
            print(f"Sources count: {len(sources)}")
            print(f"Response preview: {response[:200]}...")

            if sources:
                print(f"Sources: {sources}")
            else:
                print("❌ No sources - Claude did not use search tools")

            # Check if tools were actually called
            if len(sources) > 0:
                print("✅ Claude used tools")
            else:
                print("❌ Claude did not use tools")

        except Exception as e:
            print(f"❌ Query failed: {str(e)}")


def test_api_call_direct():
    """Test direct API call to see raw tool usage"""
    print("\n" + "="*60)
    print("Testing direct API call with tools...")
    print("="*60)

    # Initialize components
    store = VectorStore(config.CHROMA_PATH, config.EMBEDDING_MODEL, config.MAX_RESULTS)
    tool_manager = ToolManager()
    search_tool = CourseSearchTool(store)
    outline_tool = CourseOutlineTool(store)
    tool_manager.register_tool(search_tool)
    tool_manager.register_tool(outline_tool)

    ai_generator = AIGenerator(config.ANTHROPIC_API_KEY, config.ANTHROPIC_MODEL)

    # Test with a query that should definitely trigger tools
    query = "What does the MCP course cover? Give me specific details from the course content."

    try:
        response = ai_generator.generate_response(
            query=query,
            conversation_history=None,
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager
        )

        print(f"Response: {response}")

        # Check if tools were used
        sources = tool_manager.get_last_sources()
        print(f"Sources after direct API call: {sources}")

        if sources:
            print("✅ Direct API call used tools")
        else:
            print("❌ Direct API call did not use tools")

    except Exception as e:
        print(f"❌ Direct API call failed: {str(e)}")
        import traceback
        traceback.print_exc()


def test_tool_definitions():
    """Check if tool definitions are properly formatted"""
    print("\n" + "="*60)
    print("Checking tool definitions...")
    print("="*60)

    store = VectorStore(config.CHROMA_PATH, config.EMBEDDING_MODEL, config.MAX_RESULTS)
    tool_manager = ToolManager()
    search_tool = CourseSearchTool(store)
    outline_tool = CourseOutlineTool(store)
    tool_manager.register_tool(search_tool)
    tool_manager.register_tool(outline_tool)

    definitions = tool_manager.get_tool_definitions()

    print(f"Number of tools: {len(definitions)}")

    for i, defn in enumerate(definitions, 1):
        print(f"\nTool {i}:")
        print(json.dumps(defn, indent=2))

        # Validate required fields
        required_fields = ['name', 'description', 'input_schema']
        for field in required_fields:
            if field not in defn:
                print(f"❌ Missing required field: {field}")
            else:
                print(f"✅ Has {field}")


def test_system_prompt():
    """Check the system prompt content"""
    print("\n" + "="*60)
    print("Checking system prompt...")
    print("="*60)

    ai_generator = AIGenerator(config.ANTHROPIC_API_KEY, config.ANTHROPIC_MODEL)

    print("System prompt:")
    print("-" * 40)
    print(ai_generator.SYSTEM_PROMPT)
    print("-" * 40)

    # Check for key phrases that might affect tool usage
    key_phrases = [
        "search_course_content",
        "get_course_outline",
        "tool",
        "Tool Usage Guidelines",
        "One tool use per query maximum"
    ]

    for phrase in key_phrases:
        if phrase in ai_generator.SYSTEM_PROMPT:
            print(f"✅ Contains '{phrase}'")
        else:
            print(f"❌ Missing '{phrase}'")


def main():
    """Run all tests"""
    print("Claude Tool Usage Analysis")
    print("="*60)

    test_system_prompt()
    test_tool_definitions()
    test_api_call_direct()
    test_claude_tool_usage()


if __name__ == "__main__":
    main()