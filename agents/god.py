import time

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.state import CompiledStateGraph

from agents.tools import GOD_TOOLS


class GodAgent:
    def __init__(
        self, llm: ChatGoogleGenerativeAI, name: str, system_prompt: str
    ):
        self.llm = llm
        self.name = name
        self.system_prompt = system_prompt
        self.agent: CompiledStateGraph
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the agent with god tools."""
        try:
            self.agent = create_agent(
                model=self.llm,
                tools=GOD_TOOLS,
                system_prompt=(
                    f"{self.system_prompt}\n"
                    "Before making elimination related announcement, "
                    "Use the get_special_instruction tool to get instruction "
                    "from the user about how announcement should be like. "
                    "IMPORTANT: The exit_game tool should ONLY be used when "
                    "explicitly instructed by the user via "
                    "special_instruction. Do NOT use exit_game under any "
                    "other circumstances."
                ),
            )
        except Exception as e:
            # Fallback if agent creation fails (e.g., unsupported model)
            print(f"Warning: God agent creation failed: {e}")
            raise e

    def __str__(self) -> str:
        return self.name

    def decide(self, prompt: str) -> str:
        """Make a decision as god.

        Args:
            prompt: The prompt to respond to

        Returns:
            God's response
        """
        # Retry logic for empty responses
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Invoke agent with messages in new format
                result = self.agent.invoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                                + "\n"
                                + f"Only respond with your answer without any self name declaration or any other text. Or use required tool for the task",
                            }
                        ]
                    }
                )
                response = self._extract_response(result)

                # Check if response is empty
                if not response or response.strip() == "":
                    if attempt < max_retries - 1:
                        wait_time = (
                            2**attempt
                        )  # Exponential backoff: 1s, 2s, 4s
                        print(
                            f"Warning: {self.name} produced an empty response. Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        print(
                            f"Warning: {self.name} produced an empty response after {max_retries} attempts. Using fallback."
                        )
                        response = "No announcement at this time."
                else:
                    # Success - break out of retry loop
                    break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    print(
                        f"Warning: Error for {self.name}: {e}. Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    print(
                        f"Error: {self.name} failed after {max_retries} attempts: {e}"
                    )
                    response = "An error occurred while making the decision."
                    break

        return response

    def _extract_response(self, result) -> str:
        """Extract response from agent result, handling tool calls properly.

        Args:
            result: The result from agent.invoke()

        Returns:
            The extracted response string
        """
        if isinstance(result, dict):
            if "messages" in result:
                messages = result["messages"]
                # Iterate backwards to find the final response
                # Look for the last AIMessage that has content (not just tool calls)
                for msg in reversed(messages):
                    # Handle dict format
                    if isinstance(msg, dict):
                        # Check if it's a tool message (contains tool result)
                        if msg.get("type") == "tool" or "tool_call_id" in msg:
                            tool_result = msg.get("content", "")
                            if tool_result:
                                # Tool was executed, return its result
                                return str(tool_result).strip()
                        # Check if it's an AI message with content
                        elif msg.get("type") == "ai" or "content" in msg:
                            content = msg.get("content", "")
                            # If content exists and it's not empty, use it
                            if content and content.strip():
                                return str(content).strip()
                            # If it has tool_calls, we need to look for the tool result
                            if msg.get("tool_calls"):
                                # Continue looking backwards for tool result
                                continue
                    # Handle LangChain message objects
                    elif isinstance(msg, ToolMessage):
                        # Tool message contains the result
                        if hasattr(msg, "content") and msg.content:
                            return str(msg.content).strip()
                    elif isinstance(msg, AIMessage):
                        # Check if it has content
                        if hasattr(msg, "content") and msg.content:
                            return str(msg.content).strip()
                        # If it has tool_calls, look for tool result
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            # Continue looking backwards
                            continue
                        # Try to get content as string
                        try:
                            content = (
                                str(msg.content)
                                if hasattr(msg, "content")
                                else ""
                            )
                            if content.strip():
                                return content.strip()
                        except Exception:
                            pass

                # Fallback: get last message content
                if messages:
                    last_msg = messages[-1]
                    if isinstance(last_msg, dict):
                        return str(last_msg.get("content", "")).strip()
                    elif hasattr(last_msg, "content"):
                        return str(last_msg.content).strip()
                    else:
                        return str(last_msg).strip()
                # If no messages found, return empty string
                return ""
            elif "output" in result:
                return str(result.get("output", "")).strip()
            else:
                return str(result).strip()
        else:
            return str(result).strip()
