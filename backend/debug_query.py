#!/usr/bin/env python3
"""
Debug version of query to trace source handling
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import config
from rag_system import RAGSystem


def debug_query_flow():
    """Debug the query flow to see where sources are lost"""
    print("Debugging query flow...")

    rag = RAGSystem(config)

    # Reset sources first
    rag.tool_manager.reset_sources()
    print(f"1. Initial sources after reset: {rag.tool_manager.get_last_sources()}")

    # Test query
    query = "What specific examples are given in the MCP course?"
    prompt = f"Answer this question about course materials: {query}"

    print(f"2. About to call ai_generator.generate_response...")

    # Monkey patch to debug the tool execution
    original_execute_tool = rag.tool_manager.execute_tool

    def debug_execute_tool(tool_name, **kwargs):
        print(f"3. Tool '{tool_name}' being executed with: {kwargs}")
        result = original_execute_tool(tool_name, **kwargs)
        print(f"4. Tool execution result length: {len(result)}")
        sources_after_execution = rag.tool_manager.get_last_sources()
        print(f"5. Sources immediately after tool execution: {sources_after_execution}")
        return result

    rag.tool_manager.execute_tool = debug_execute_tool

    try:
        # Generate response using AI with tools
        response = rag.ai_generator.generate_response(
            query=prompt,
            conversation_history=None,
            tools=rag.tool_manager.get_tool_definitions(),
            tool_manager=rag.tool_manager,
        )

        print(f"6. AI generator returned, response length: {len(response)}")

        # Get sources and source links from the search tool
        sources = rag.tool_manager.get_last_sources()
        source_links = rag.tool_manager.get_last_source_links()

        print(f"7. Sources retrieved: {sources}")
        print(f"8. Source links retrieved: {source_links}")

        # Reset sources after retrieving them
        rag.tool_manager.reset_sources()

        print(f"9. Final result - Response: {response[:100]}...")
        print(f"10. Final sources: {sources}")

        return response, sources, source_links

    finally:
        # Restore original method
        rag.tool_manager.execute_tool = original_execute_tool


def test_direct_tool_execution():
    """Test tool execution directly"""
    print("\n" + "=" * 60)
    print("Testing direct tool execution...")
    print("=" * 60)

    rag = RAGSystem(config)

    # Reset sources
    rag.tool_manager.reset_sources()
    print(f"Initial sources: {rag.tool_manager.get_last_sources()}")

    # Execute tool directly
    result = rag.tool_manager.execute_tool(
        "search_course_content", query="MCP examples"
    )
    print(f"Direct execution result length: {len(result)}")

    # Check sources immediately
    sources = rag.tool_manager.get_last_sources()
    source_links = rag.tool_manager.get_last_source_links()

    print(f"Sources after direct execution: {sources}")
    print(f"Source links after direct execution: {source_links}")


def main():
    test_direct_tool_execution()
    debug_query_flow()


if __name__ == "__main__":
    main()
