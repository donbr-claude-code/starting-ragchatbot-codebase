#!/usr/bin/env python3
"""
Test the actual API endpoint to see if there are issues there
"""

import json
import os
import sys

import requests

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))


def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Health endpoint status: {response.status_code}")
        print(f"Health response: {response.json()}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False


def test_query_endpoint():
    """Test the query endpoint with different types of queries"""
    queries_to_test = [
        "What is machine learning?",  # General knowledge - should not use tools
        "What examples are given in the MCP course?",  # Specific content - should use tools
        "Give me the outline of the Computer Use course",  # Should use outline tool
        "Hello",  # Simple greeting - should not use tools
    ]

    for i, query in enumerate(queries_to_test, 1):
        print(f"\n{'-'*60}")
        print(f"API Test {i}: {query}")
        print("-" * 60)

        payload = {"query": query, "session_id": f"test_session_{i}"}

        try:
            response = requests.post(
                "http://localhost:8000/api/query",
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            print(f"Status code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"Answer length: {len(data.get('answer', ''))}")
                print(f"Sources count: {len(data.get('sources', []))}")
                print(f"Source links count: {len(data.get('source_links', {}))}")
                print(f"Session ID: {data.get('session_id')}")

                if data.get("sources"):
                    print(f"Sources: {data['sources']}")
                    print("✅ Query used tools successfully")
                else:
                    print("❌ Query did not use tools")

                print(f"Answer preview: {data.get('answer', '')[:200]}...")

            else:
                print(f"❌ API call failed: {response.status_code}")
                print(f"Error: {response.text}")

        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server")
            return False
        except Exception as e:
            print(f"❌ API test failed: {str(e)}")

    return True


def test_courses_endpoint():
    """Test the courses analytics endpoint"""
    print(f"\n{'-'*60}")
    print("Testing /api/courses endpoint")
    print("-" * 60)

    try:
        response = requests.get("http://localhost:8000/api/courses")
        print(f"Status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Total courses: {data.get('total_courses')}")
            print(f"Course titles: {data.get('course_titles')}")
            return True
        else:
            print(f"❌ Courses endpoint failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Courses endpoint test failed: {str(e)}")
        return False


def test_error_cases():
    """Test error cases"""
    print(f"\n{'-'*60}")
    print("Testing error cases")
    print("-" * 60)

    # Test empty query
    try:
        response = requests.post(
            "http://localhost:8000/api/query",
            json={"query": ""},
            headers={"Content-Type": "application/json"},
        )
        print(f"Empty query status: {response.status_code}")

        # Test malformed request
        response = requests.post(
            "http://localhost:8000/api/query",
            json={"invalid": "data"},
            headers={"Content-Type": "application/json"},
        )
        print(f"Malformed request status: {response.status_code}")

    except Exception as e:
        print(f"❌ Error case testing failed: {str(e)}")


def main():
    print("API Endpoint Testing")
    print("=" * 60)

    # Check if server is running
    if not test_health_endpoint():
        print("\n❌ Server is not running. Please start the server first:")
        print("cd backend && uv run uvicorn app:app --reload --port 8000")
        return

    # Test main functionality
    test_courses_endpoint()
    test_query_endpoint()
    test_error_cases()

    print(f"\n{'='*60}")
    print("API Testing Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
