from typing import Any, Dict, List, Optional

import anthropic
from config import config


class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive search tools for course information.

Available Tools:
1. **search_course_content**: For searching specific course content and materials
2. **get_course_outline**: For retrieving course outlines, including course title, course link, and complete lesson lists

CRITICAL: You MUST use tools for ANY question related to courses, even if you think you know the answer from your training data. The course database contains the most current and accurate information.

Tool Usage Guidelines:
- Use **search_course_content** for questions about specific course content, examples, lessons, concepts, or any detailed educational materials
- Use **get_course_outline** for questions about course structure, lesson lists, course overviews, outlines, or when users ask "what's in this course", "what does X course cover", "give me the outline", etc.
- **ALWAYS use tools for course-related queries** - Do not rely on your general knowledge about courses
- **Sequential tool usage available**: You can make follow-up tool calls based on initial results to:
  * Search for related information if initial results are incomplete
  * Get course outlines after finding specific content to provide broader context
  * Refine searches with better course/lesson filters based on discovered information
  * Compare information across different courses or lessons
- **Maximum 2 tool rounds allowed** - Use them strategically for complex queries
- Synthesize tool results into accurate, fact-based responses
- If tools yield no results, state this clearly without offering alternatives

Response Protocol:
- **Course-related questions** (any mention of courses, lessons, content, outlines): ALWAYS use appropriate tool first
- **Pure general knowledge questions** (math, science facts unrelated to these specific courses): Answer directly without tools
- **Greetings and casual conversation**: Answer directly without tools
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool explanations, or question-type analysis
 - Do not mention "based on the search results" or "using the outline tool"

When responding to course outline queries, always include:
- Course title
- Course link
- Number and title of each lesson

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {"model": self.model, "temperature": 0, "max_tokens": 800}

    def generate_response(
        self,
        query: str,
        conversation_history: Optional[str] = None,
        tools: Optional[List] = None,
        tool_manager=None,
    ) -> str:
        """
        Generate AI response with optional tool usage and conversation context.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content,
        }

        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}

        # Get response from Claude
        response = self.client.messages.create(**api_params)

        # Handle tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_sequential_tool_execution(
                response, api_params, tool_manager
            )

        # Return direct response
        return response.content[0].text

    def _handle_sequential_tool_execution(
        self, initial_response, base_params: Dict[str, Any], tool_manager
    ):
        """
        Handle sequential tool execution with up to max_rounds of tool calls.

        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters
            tool_manager: Manager to execute tools

        Returns:
            Final response text after all tool execution rounds
        """
        messages = base_params["messages"].copy()
        current_round = 1
        current_response = initial_response
        max_rounds = config.MAX_TOOL_ROUNDS

        while (
            current_round <= max_rounds and current_response.stop_reason == "tool_use"
        ):
            # Add AI's tool use response to message chain
            messages.append({"role": "assistant", "content": current_response.content})

            # Execute all tool calls from this round
            tool_results = []
            for content_block in current_response.content:
                if content_block.type == "tool_use":
                    try:
                        tool_result = tool_manager.execute_tool(
                            content_block.name, **content_block.input
                        )
                    except Exception as e:
                        tool_result = (
                            f"Error executing tool {content_block.name}: {str(e)}"
                        )

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": tool_result,
                        }
                    )

            # Add tool results to message chain
            if tool_results:
                messages.append({"role": "user", "content": tool_results})

            # Prepare next API call
            next_params = {
                **self.base_params,
                "messages": messages,
                "system": self._get_round_aware_system_prompt(
                    base_params["system"], current_round, max_rounds
                ),
            }

            # Include tools if we haven't reached max rounds
            if current_round < max_rounds:
                next_params["tools"] = base_params.get("tools", [])
                next_params["tool_choice"] = {"type": "auto"}

            # Make next API call
            try:
                current_response = self.client.messages.create(**next_params)
                current_round += 1
            except Exception as e:
                # API error - fallback to current message chain
                return f"I encountered an error while processing your request: {str(e)}"

        # Final response without tool use or max rounds reached
        if current_response.stop_reason != "tool_use":
            return current_response.content[0].text
        else:
            # Max rounds reached but Claude still wants tools - make final call without tools
            messages.append({"role": "assistant", "content": current_response.content})
            final_params = {
                **self.base_params,
                "messages": messages,
                "system": base_params["system"],
            }
            try:
                final_response = self.client.messages.create(**final_params)
                return final_response.content[0].text
            except Exception as e:
                return f"I encountered an error while providing the final response: {str(e)}"

    def _get_round_aware_system_prompt(
        self, base_system: str, current_round: int, max_rounds: int
    ) -> str:
        """Add round-aware guidance to system prompt"""
        if current_round < max_rounds:
            addition = f"\n\nTool Round {current_round}/{max_rounds}: You can make additional tool calls if needed based on previous results."
        else:
            addition = f"\n\nFinal Round {current_round}/{max_rounds}: This is your last chance to use tools before providing the final response."

        return base_system + addition
