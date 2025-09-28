#!/usr/bin/env python3
"""
Debug script to test the RAG system components independently.
This script helps identify where the "query failed" issue is occurring.
"""

import sys
import os
import traceback
import json
from typing import Dict, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import config
from rag_system import RAGSystem
from vector_store import VectorStore
from search_tools import CourseSearchTool, CourseOutlineTool, ToolManager
from ai_generator import AIGenerator


def test_component(name: str, test_func):
    """Test a component and print results"""
    print(f"\n{'='*50}")
    print(f"Testing: {name}")
    print('='*50)

    try:
        result = test_func()
        print(f"✅ SUCCESS: {name}")
        if result:
            print(f"Result: {result}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {name}")
        print(f"Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


def test_config():
    """Test configuration"""
    print(f"ANTHROPIC_API_KEY: {'✅ Set' if config.ANTHROPIC_API_KEY else '❌ Missing'}")
    print(f"ANTHROPIC_MODEL: {config.ANTHROPIC_MODEL}")
    print(f"EMBEDDING_MODEL: {config.EMBEDDING_MODEL}")
    print(f"CHROMA_PATH: {config.CHROMA_PATH}")
    print(f"Database exists: {'✅ Yes' if os.path.exists(config.CHROMA_PATH) else '❌ No'}")
    return True


def test_vector_store():
    """Test vector store initialization and basic operations"""
    store = VectorStore(config.CHROMA_PATH, config.EMBEDDING_MODEL, config.MAX_RESULTS)

    # Test basic operations
    course_count = store.get_course_count()
    print(f"Course count: {course_count}")

    course_titles = store.get_existing_course_titles()
    print(f"Course titles: {course_titles}")

    if course_count > 0:
        # Test search
        results = store.search("machine learning")
        print(f"Search results count: {len(results.documents)}")
        print(f"Search error: {results.error}")
        if results.documents:
            print(f"First result preview: {results.documents[0][:100]}...")

    return f"Found {course_count} courses"


def test_search_tools():
    """Test search tools"""
    store = VectorStore(config.CHROMA_PATH, config.EMBEDDING_MODEL, config.MAX_RESULTS)
    search_tool = CourseSearchTool(store)
    outline_tool = CourseOutlineTool(store)

    # Test tool definitions
    search_def = search_tool.get_tool_definition()
    outline_def = outline_tool.get_tool_definition()

    print(f"Search tool name: {search_def.get('name')}")
    print(f"Outline tool name: {outline_def.get('name')}")

    # Test search execution
    search_result = search_tool.execute("machine learning")
    print(f"Search tool result length: {len(search_result)}")

    # Test outline execution with course resolution
    course_titles = store.get_existing_course_titles()
    if course_titles:
        first_course = course_titles[0]
        outline_result = outline_tool.execute(first_course)
        print(f"Outline tool result length: {len(outline_result)}")

    return "Search tools operational"


def test_tool_manager():
    """Test tool manager"""
    store = VectorStore(config.CHROMA_PATH, config.EMBEDDING_MODEL, config.MAX_RESULTS)
    tool_manager = ToolManager()

    # Register tools
    search_tool = CourseSearchTool(store)
    outline_tool = CourseOutlineTool(store)
    tool_manager.register_tool(search_tool)
    tool_manager.register_tool(outline_tool)

    # Test tool definitions
    definitions = tool_manager.get_tool_definitions()
    print(f"Number of registered tools: {len(definitions)}")

    for defn in definitions:
        print(f"- {defn.get('name')}: {defn.get('description', 'No description')}")

    # Test tool execution
    result = tool_manager.execute_tool("search_course_content", query="machine learning")
    print(f"Tool execution result length: {len(result)}")

    # Check sources
    sources = tool_manager.get_last_sources()
    print(f"Last sources count: {len(sources)}")

    return f"Tool manager has {len(definitions)} tools"


def test_ai_generator():
    """Test AI generator (without actual API call)"""
    generator = AIGenerator(config.ANTHROPIC_API_KEY, config.ANTHROPIC_MODEL)

    # Check initialization
    print(f"Model: {generator.model}")
    print(f"Base params: {generator.base_params}")
    print(f"System prompt length: {len(generator.SYSTEM_PROMPT)}")

    # Check if system prompt contains tool info
    has_search_tool = "search_course_content" in generator.SYSTEM_PROMPT
    has_outline_tool = "get_course_outline" in generator.SYSTEM_PROMPT

    print(f"System prompt has search tool info: {'✅' if has_search_tool else '❌'}")
    print(f"System prompt has outline tool info: {'✅' if has_outline_tool else '❌'}")

    return "AI generator initialized"


def test_rag_system():
    """Test RAG system initialization"""
    rag = RAGSystem(config)

    # Test analytics
    analytics = rag.get_course_analytics()
    print(f"Total courses: {analytics['total_courses']}")
    print(f"Course titles: {analytics['course_titles']}")

    # Test tool manager
    tool_defs = rag.tool_manager.get_tool_definitions()
    print(f"Available tools: {[t['name'] for t in tool_defs]}")

    return f"RAG system ready with {analytics['total_courses']} courses"


def test_real_query():
    """Test a real query through the system (this might fail)"""
    rag = RAGSystem(config)

    try:
        response, sources, source_links = rag.query("What is machine learning?")
        print(f"Response length: {len(response)}")
        print(f"Sources count: {len(sources)}")
        print(f"Response preview: {response[:200]}...")
        return "Query executed successfully"
    except Exception as e:
        print(f"Query failed with error: {str(e)}")
        raise


def test_direct_tool_execution():
    """Test direct tool execution without AI"""
    rag = RAGSystem(config)

    # Test search tool directly
    search_result = rag.tool_manager.execute_tool(
        "search_course_content",
        query="machine learning"
    )
    print(f"Direct search result length: {len(search_result)}")
    print(f"Search result preview: {search_result[:200]}...")

    sources = rag.tool_manager.get_last_sources()
    print(f"Sources after search: {sources}")

    return "Direct tool execution works"


def main():
    """Run all diagnostic tests"""
    print("RAG System Diagnostic Tool")
    print("="*50)

    tests = [
        ("Configuration", test_config),
        ("Vector Store", test_vector_store),
        ("Search Tools", test_search_tools),
        ("Tool Manager", test_tool_manager),
        ("AI Generator", test_ai_generator),
        ("RAG System", test_rag_system),
        ("Direct Tool Execution", test_direct_tool_execution),
        ("Real Query (might fail)", test_real_query),
    ]

    results = {}
    for name, test_func in tests:
        results[name] = test_component(name, test_func)

    print(f"\n{'='*50}")
    print("SUMMARY")
    print('='*50)

    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")

    failed_tests = [name for name, success in results.items() if not success]
    if failed_tests:
        print(f"\n❌ Failed tests: {', '.join(failed_tests)}")
        print("These components need investigation.")
    else:
        print(f"\n✅ All tests passed! The issue might be elsewhere.")


if __name__ == "__main__":
    main()