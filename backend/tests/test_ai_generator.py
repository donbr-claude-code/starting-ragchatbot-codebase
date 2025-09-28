import pytest
from unittest.mock import Mock, patch, MagicMock
from ai_generator import AIGenerator
from config import config


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

    def test_handle_sequential_tool_execution_multiple_tools(self):
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

            result = generator._handle_sequential_tool_execution(
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
            assert "Maximum 2 tool rounds allowed" in generator.SYSTEM_PROMPT
            assert "Sequential tool usage available" in generator.SYSTEM_PROMPT

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

            result = generator._handle_sequential_tool_execution(
                initial_response,
                base_params,
                mock_tool_manager
            )

            # Should not execute any tools
            mock_tool_manager.execute_tool.assert_not_called()

            # Should still return a response
            assert result == "Response without tool execution"

    def test_sequential_tool_usage(self):
        """Test that Claude can make sequential tool calls in separate rounds"""
        api_key = "test-api-key"
        model = "claude-3-sonnet-20240229"

        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Mock first tool response (round 1)
            round1_response = Mock()
            round1_response.stop_reason = "tool_use"

            tool_content_1 = Mock()
            tool_content_1.type = "tool_use"
            tool_content_1.name = "search_course_content"
            tool_content_1.id = "tool_1"
            tool_content_1.input = {"query": "neural networks"}
            round1_response.content = [tool_content_1]

            # Mock second tool response (round 2)
            round2_response = Mock()
            round2_response.stop_reason = "tool_use"

            tool_content_2 = Mock()
            tool_content_2.type = "tool_use"
            tool_content_2.name = "get_course_outline"
            tool_content_2.id = "tool_2"
            tool_content_2.input = {"course_name": "ML Course"}
            round2_response.content = [tool_content_2]

            # Mock final response (round 3 - no tools)
            final_response = Mock()
            final_response.stop_reason = "end_turn"
            final_response.content = [Mock(text="Sequential response based on both searches")]

            # Setup sequence of responses
            mock_client.messages.create.side_effect = [round1_response, round2_response, final_response]

            generator = AIGenerator(api_key, model)

            # Mock tool manager
            mock_tool_manager = Mock()
            mock_tool_manager.execute_tool.side_effect = [
                "Neural networks found in ML course",
                "ML Course outline with lessons"
            ]

            tools = [
                {"name": "search_course_content", "description": "Search courses"},
                {"name": "get_course_outline", "description": "Get course outline"}
            ]

            result = generator.generate_response(
                "Tell me about neural networks and give me the course outline",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Verify both tools were executed
            assert mock_tool_manager.execute_tool.call_count == 2
            mock_tool_manager.execute_tool.assert_any_call("search_course_content", query="neural networks")
            mock_tool_manager.execute_tool.assert_any_call("get_course_outline", course_name="ML Course")

            # Verify 3 API calls were made (2 tool rounds + final)
            assert mock_client.messages.create.call_count == 3

            # Verify final response
            assert result == "Sequential response based on both searches"

    def test_single_round_unchanged(self):
        """Test that single tool usage still works as before"""
        api_key = "test-api-key"
        model = "claude-3-sonnet-20240229"

        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Mock single tool response
            tool_response = Mock()
            tool_response.stop_reason = "tool_use"

            tool_content = Mock()
            tool_content.type = "tool_use"
            tool_content.name = "search_course_content"
            tool_content.id = "tool_1"
            tool_content.input = {"query": "test"}
            tool_response.content = [tool_content]

            # Mock final response
            final_response = Mock()
            final_response.stop_reason = "end_turn"
            final_response.content = [Mock(text="Single tool response")]

            mock_client.messages.create.side_effect = [tool_response, final_response]

            generator = AIGenerator(api_key, model)
            mock_tool_manager = Mock()
            mock_tool_manager.execute_tool.return_value = "Tool result"

            tools = [{"name": "search_course_content", "description": "Search"}]

            result = generator.generate_response(
                "What is machine learning?",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Verify only one tool execution
            assert mock_tool_manager.execute_tool.call_count == 1
            # Verify only 2 API calls (tool + final)
            assert mock_client.messages.create.call_count == 2
            assert result == "Single tool response"

    def test_max_rounds_termination(self):
        """Test that system enforces maximum 2 tool rounds"""
        api_key = "test-api-key"
        model = "claude-3-sonnet-20240229"

        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Mock responses for 2 tool rounds + final forced response
            tool_response_1 = Mock()
            tool_response_1.stop_reason = "tool_use"
            tool_content_1 = Mock()
            tool_content_1.type = "tool_use"
            tool_content_1.name = "search_course_content"
            tool_content_1.id = "tool_1"
            tool_content_1.input = {"query": "test1"}
            tool_response_1.content = [tool_content_1]

            tool_response_2 = Mock()
            tool_response_2.stop_reason = "tool_use"
            tool_content_2 = Mock()
            tool_content_2.type = "tool_use"
            tool_content_2.name = "search_course_content"
            tool_content_2.id = "tool_2"
            tool_content_2.input = {"query": "test2"}
            tool_response_2.content = [tool_content_2]

            # Claude still wants tools after 2 rounds - should be forced to final response
            still_wants_tools = Mock()
            still_wants_tools.stop_reason = "tool_use"
            still_wants_tools.content = [Mock(type="tool_use")]

            # Forced final response without tools
            forced_final = Mock()
            forced_final.content = [Mock(text="Forced final response")]

            mock_client.messages.create.side_effect = [
                tool_response_1, tool_response_2, still_wants_tools, forced_final
            ]

            generator = AIGenerator(api_key, model)
            mock_tool_manager = Mock()
            mock_tool_manager.execute_tool.return_value = "Tool result"

            tools = [{"name": "search_course_content", "description": "Search"}]

            result = generator.generate_response(
                "Complex query",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Verify exactly 2 tool executions (max rounds)
            assert mock_tool_manager.execute_tool.call_count == 2
            # Verify 4 API calls (2 tool rounds + still wants tools + forced final)
            assert mock_client.messages.create.call_count == 4
            assert result == "Forced final response"

    def test_natural_termination(self):
        """Test that system terminates naturally when Claude doesn't use tools"""
        api_key = "test-api-key"
        model = "claude-3-sonnet-20240229"

        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Mock direct response without tools
            direct_response = Mock()
            direct_response.stop_reason = "end_turn"
            direct_response.content = [Mock(text="Direct answer without tools")]

            mock_client.messages.create.return_value = direct_response

            generator = AIGenerator(api_key, model)
            mock_tool_manager = Mock()

            tools = [{"name": "search_course_content", "description": "Search"}]

            result = generator.generate_response(
                "What is 2+2?",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Verify no tool executions
            mock_tool_manager.execute_tool.assert_not_called()
            # Verify only 1 API call
            assert mock_client.messages.create.call_count == 1
            assert result == "Direct answer without tools"

    def test_tool_error_handling(self):
        """Test graceful handling of tool execution errors"""
        api_key = "test-api-key"
        model = "claude-3-sonnet-20240229"

        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Mock tool response
            tool_response = Mock()
            tool_response.stop_reason = "tool_use"
            tool_content = Mock()
            tool_content.type = "tool_use"
            tool_content.name = "search_course_content"
            tool_content.id = "tool_1"
            tool_content.input = {"query": "test"}
            tool_response.content = [tool_content]

            # Mock final response
            final_response = Mock()
            final_response.stop_reason = "end_turn"
            final_response.content = [Mock(text="Response after error")]

            mock_client.messages.create.side_effect = [tool_response, final_response]

            generator = AIGenerator(api_key, model)

            # Mock tool manager that raises an error
            mock_tool_manager = Mock()
            mock_tool_manager.execute_tool.side_effect = Exception("Tool failed")

            tools = [{"name": "search_course_content", "description": "Search"}]

            result = generator.generate_response(
                "Test query",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Verify tool was attempted
            assert mock_tool_manager.execute_tool.call_count == 1
            # Verify system continued and got final response
            assert mock_client.messages.create.call_count == 2
            assert result == "Response after error"

            # Verify error was passed to Claude in tool results
            final_call_args = mock_client.messages.create.call_args_list[1][1]
            messages = final_call_args["messages"]
            tool_results_message = messages[2]  # User message with tool results
            assert "Error executing tool" in str(tool_results_message["content"])
            assert "Tool failed" in str(tool_results_message["content"])