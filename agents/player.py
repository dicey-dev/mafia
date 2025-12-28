from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from agents.tools import (
    DETECTIVE_TOOLS,
    HEALER_TOOLS,
    MAFIA_TOOLS,
    PLAYER_TOOLS,
)
from game.types import Role


class PlayerAgent(BaseModel):
    name: str
    role: Role | None = None
    alive: bool = True
    system_prompt: str
    llm: ChatGoogleGenerativeAI
    memory: list[str] = []
    public_logs: list[str] = []
    private_logs: list[str] = []
    agent = None

    def __init__(self, **data):
        super().__init__(**data)
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the agent with appropriate tools."""
        # Select tools based on role
        if self.role == Role.MAFIA:
            tools = MAFIA_TOOLS
        elif self.role == Role.HEALER:
            tools = HEALER_TOOLS
        elif self.role == Role.DETECTIVE:
            tools = DETECTIVE_TOOLS
        else:
            tools = PLAYER_TOOLS

        try:
            # Create agent using new LangChain API
            self.agent = create_agent(
                model=self.llm,
                tools=tools,
                system_prompt=self.system_prompt,
            )
        except Exception as e:
            # Fallback if agent creation fails (e.g., unsupported model)
            print(f"Warning: Agent creation failed for {self.name}: {e}")
            self.agent = None

    def _get_full_memory(self) -> list[str]:
        """Combine public and private logs for context."""
        combined = self.public_logs + self.private_logs + self.memory
        return combined

    def speak(self, prompt: str, use_tools: bool = True) -> str:
        """Speak as the player agent.

        Args:
            prompt: The prompt to respond to
            use_tools: Whether to use tools (False for simple responses)

        Returns:
            The agent's response
        """
        if use_tools and self.agent:
            # Build messages list in the format expected by new API
            messages = []
            # Add chat history from memory
            for msg in self._get_full_memory():
                messages.append({"role": "user", "content": msg})
            # Add current prompt
            messages.append({"role": "user", "content": prompt})

            # Invoke agent
            result = self.agent.invoke({"messages": messages})
            # Extract response from the result
            # Result format may vary, try common patterns
            if isinstance(result, dict):
                if "messages" in result:
                    # Get last message from messages array
                    last_msg = result["messages"][-1]
                    if isinstance(last_msg, dict):
                        response = last_msg.get("content", "").strip()
                    else:
                        response = str(last_msg.content).strip()
                elif "output" in result:
                    response = result.get("output", "").strip()
                else:
                    response = str(result).strip()
            else:
                response = str(result).strip()
        else:
            # Fallback to simple LLM call
            messages = [
                SystemMessage(content=self.system_prompt),
                *[HumanMessage(content=m) for m in self._get_full_memory()],
                HumanMessage(content=prompt),
            ]
            response = str(self.llm.invoke(messages).content).strip()

        # Store response in memory
        self.memory.append(f"[{self.name}]: {response}")
        return response

    def add_public_log(self, message: str):
        """Add a public log visible to all players."""
        self.public_logs.append(message)

    def add_private_log(self, message: str):
        """Add a private log only visible to this player."""
        self.private_logs.append(message)

    def sync_logs(self, game_logs: list[str]):
        """Sync game logs to player's public memory."""
        for log in game_logs:
            if log not in self.public_logs:
                self.public_logs.append(log)
