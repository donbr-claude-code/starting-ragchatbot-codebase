import pytest
from unittest.mock import Mock, patch, MagicMock
from ai_generator import AIGenerator


class TestAIGenerator:
    """Test AIGenerator functionality"""

    def test_initialization(self):
        """Test AIGenerator initialization"""
        api_key = "test-api-key"
        model = "claude-3-sonnet-20240229"

        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic:
            generator = AIGenerator(api_key, model)

            mock_anthropic.assert_called_once_with(api_key=api_key)
            assert generator.model == model
            assert generator.base_params["model"] == model
            assert generator.base_params["temperature"] == 0
            assert generator.base_params["max_tokens"] == 800

    def test_generate_response_without_tools(self):
        """Test response generation without tools"""
        api_key = "test-api-key"
        model = "claude-3-sonnet-20240229"

        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Mock successful response
            mock_response = Mock()
            mock_response.content = [Mock(text="This is a test response")]
            mock_response.stop_reason = "end_turn"
            mock_client.messages.create.return_value = mock_response

            generator = AIGenerator(api_key, model)
            result = generator.generate_response("What is machine learning?")

            # Verify the API call
            mock_client.messages.create.assert_called_once()
            call_args = mock_client.messages.create.call_args[1]

            assert call_args["model"] == model
            assert call_args["temperature"] == 0
            assert call_args["max_tokens"] == 800
            assert len(call_args["messages"]) == 1
            assert call_args["messages"][0]["role"] == "user"
            assert call_args["messages"][0]["content"] == "What is machine learning?"
            assert generator.SYSTEM_PROMPT in call_args["system"]

            # Verify response
            assert result == "This is a test response"

    def test_generate_response_with_conversation_history(self):
        """Test response generation with conversation history"""
        api_key = "test-api-key"
        model = "claude-3-sonnet-20240229"

        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            mock_response = Mock()
            mock_response.content = [Mock(text="Follow-up response")]
            mock_response.stop_reason = "end_turn"
            mock_client.messages.create.return_value = mock_response

            generator = AIGenerator(api_key, model)
            history = "Previous Q: What is AI?\nA: AI is artificial intelligence."

            result = generator.generate_response(
                "Tell me more about neural networks",
                conversation_history=history
            )

            # Verify conversation history is included in system prompt
            call_args = mock_client.messages.create.call_args[1]
            assert history in call_args["system"]

    def test_generate_response_with_tools_no_tool_use(self):
        """Test response generation with tools available but not used"""
        api_key = "test-api-key"
        model = "claude-3-sonnet-20240229"

        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            mock_response = Mock()
            mock_response.content = [Mock(text="Direct response without tools")]
            mock_response.stop_reason = "end_turn"
            mock_client.messages.create.return_value = mock_response

            generator = AIGenerator(api_key, model)

            # Mock tool definitions
            tools = [
                {
                    "name": "search_course_content",
                    "description": "Search course materials",
                    "input_schema": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"]
                    }
                }
            ]

            result = generator.generate_response(
                "What is 2+2?",
                tools=tools
            )

            # Verify tools were included in API call
            call_args = mock_client.messages.create.call_args[1]
            assert "tools" in call_args
            assert call_args["tools"] == tools
            assert call_args["tool_choice"] == {"type": "auto"}

            assert result == "Direct response without tools"

    def test_generate_response_with_tool_use(self):
        """Test response generation with tool use"""
        api_key = "test-api-key"
        model = "claude-3-sonnet-20240229"

        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Mock tool use response
            tool_use_response = Mock()
            tool_use_response.stop_reason = "tool_use"

            # Mock tool use content block
            tool_content = Mock()
            tool_content.type = "tool_use"
            tool_content.name = "search_course_content"
            tool_content.id = "tool_use_123"
            tool_content.input = {"query": "machine learning"}

            tool_use_response.content = [tool_content]

            # Mock final response after tool execution
            final_response = Mock()
            final_response.content = [Mock(text="Response based on search results")]

            # Setup sequence of responses
            mock_client.messages.create.side_effect = [tool_use_response, final_response]

            generator = AIGenerator(api_key, model)

            # Mock tool manager
            mock_tool_manager = Mock()
            mock_tool_manager.execute_tool.return_value = "Search results: ML is a subset of AI"

            tools = [
                {
                    "name": "search_course_content",
                    "description": "Search course materials",
                    "input_schema": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"]
                    }
                }
            ]

            result = generator.generate_response(
                "What is machine learning?",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Verify tool was executed
            mock_tool_manager.execute_tool.assert_called_once_with(
                "search_course_content",
                query="machine learning"
            )

            # Verify final response
            assert result == "Response based on search results"

            # Verify two API calls were made
            assert mock_client.messages.create.call_count == 2

    def test_handle_tool_execution_multiple_tools(self):
        """Test handling of multiple tool calls in one response"""
        api_key = "test-api-key"
        model = "claude-3-sonnet-20240229"

        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            generator = AIGenerator(api_key, model)

            # Mock initial response with multiple tool uses
            initial_response = Mock()
            initial_response.stop_reason = "tool_use"

            tool_content_1 = Mock()
            tool_content_1.type = "tool_use"
            tool_content_1.name = "search_course_content"
            tool_content_1.id = "tool_1"
            tool_content_1.input = {"query": "ML"}

            tool_content_2 = Mock()
            tool_content_2.type = "tool_use"
            tool_content_2.name = "get_course_outline"
            tool_content_2.id = "tool_2"
            tool_content_2.input = {"course_name": "ML Course"}

            initial_response.content = [tool_content_1, tool_content_2]

            # Mock tool manager
            mock_tool_manager = Mock()
            mock_tool_manager.execute_tool.side_effect = [
                "ML search results",
                "Course outline results"
            ]

            # Mock base params
            base_params = {
                "messages": [{"role": "user", "content": "test query"}],
                "system": "test system prompt",
                "model": model,
                "temperature": 0,
                "max_tokens": 800
            }

            # Mock final response
            final_response = Mock()
            final_response.content = [Mock(text="Combined response")]
            mock_client.messages.create.return_value = final_response

            result = generator._handle_tool_execution(
                initial_response,
                base_params,
                mock_tool_manager
            )

            # Verify both tools were executed
            assert mock_tool_manager.execute_tool.call_count == 2
            mock_tool_manager.execute_tool.assert_any_call("search_course_content", query="ML")
            mock_tool_manager.execute_tool.assert_any_call("get_course_outline", course_name="ML Course")

            # Verify final API call structure
            final_call_args = mock_client.messages.create.call_args[1]
            assert len(final_call_args["messages"]) == 3  # Original + assistant + tool results

            # Check tool results message
            tool_results_message = final_call_args["messages"][2]
            assert tool_results_message["role"] == "user"
            assert len(tool_results_message["content"]) == 2  # Two tool results

            assert result == "Combined response"

    def test_system_prompt_content(self):
        """Test that system prompt contains expected content"""
        api_key = "test-api-key"
        model = "claude-3-sonnet-20240229"

        with patch('ai_generator.anthropic.Anthropic'):
            generator = AIGenerator(api_key, model)

            # Check system prompt contains tool usage guidelines
            assert "search_course_content" in generator.SYSTEM_PROMPT
            assert "get_course_outline" in generator.SYSTEM_PROMPT
            assert "Tool Usage Guidelines" in generator.SYSTEM_PROMPT
            assert "One tool use per query maximum" in generator.SYSTEM_PROMPT

    def test_api_error_handling(self):
        """Test handling of API errors"""
        api_key = "test-api-key"
        model = "claude-3-sonnet-20240229"

        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Mock API error
            mock_client.messages.create.side_effect = Exception("API Error")

            generator = AIGenerator(api_key, model)

            # Should propagate the exception
            with pytest.raises(Exception, match="API Error"):
                generator.generate_response("test query")

    def test_invalid_tool_response(self):
        """Test handling of invalid tool response format"""
        api_key = "test-api-key"
        model = "claude-3-sonnet-20240229"

        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            generator = AIGenerator(api_key, model)

            # Mock initial response with invalid tool content
            initial_response = Mock()
            initial_response.stop_reason = "tool_use"

            invalid_content = Mock()
            invalid_content.type = "text"  # Not a tool_use type
            initial_response.content = [invalid_content]

            mock_tool_manager = Mock()

            base_params = {
                "messages": [{"role": "user", "content": "test"}],
                "system": "test system",
                "model": model,
                "temperature": 0,
                "max_tokens": 800
            }

            # Mock final response
            final_response = Mock()
            final_response.content = [Mock(text="Response without tool execution")]
            mock_client.messages.create.return_value = final_response

            result = generator._handle_tool_execution(
                initial_response,
                base_params,
                mock_tool_manager
            )

            # Should not execute any tools
            mock_tool_manager.execute_tool.assert_not_called()

            # Should still return a response
            assert result == "Response without tool execution"