import random
import re

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.player import PlayerAgent
from agents.tools import GOD_TOOLS
from game.types import Role


class GodAgent:
    def __init__(
        self, llm: ChatGoogleGenerativeAI, name: str, system_prompt: str
    ):
        self.llm = llm
        self.name = f"GOD [{name}]"
        self.system_prompt = system_prompt
        self.agent = None
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the agent with god tools."""
        try:
            self.agent = create_agent(
                model=self.llm,
                tools=GOD_TOOLS,
                system_prompt=self.system_prompt,
            )
        except Exception as e:
            # Fallback if agent creation fails (e.g., unsupported model)
            print(f"Warning: God agent creation failed: {e}")
            self.agent = None

    def __str__(self) -> str:
        return self.name

    def decide(self, prompt: str, use_tools: bool = True) -> str:
        """Make a decision as god.

        Args:
            prompt: The prompt to respond to
            use_tools: Whether to use tools

        Returns:
            God's response
        """
        if use_tools and self.agent:
            # Invoke agent with messages in new format
            result = self.agent.invoke(
                {"messages": [{"role": "user", "content": prompt}]}
            )
            # Extract response from the result
            if isinstance(result, dict):
                if "messages" in result:
                    # Get last message from messages array
                    last_msg = result["messages"][-1]
                    if isinstance(last_msg, dict):
                        return last_msg.get("content", "").strip()
                    else:
                        return str(last_msg.content).strip()
                elif "output" in result:
                    return result.get("output", "").strip()
                else:
                    return str(result).strip()
            else:
                return str(result).strip()
        else:
            return str(
                self.llm.invoke(
                    [
                        SystemMessage(content=self.system_prompt),
                        HumanMessage(content=prompt),
                    ]
                ).content
            ).strip()

    def _normalize_name(self, text: str) -> str:
        """Normalize LLM output to improve matching."""
        return re.sub(r"\s+", " ", text.strip())

    def collect_votes(
        self, role: Role, players: list[PlayerAgent], proposals: list[str]
    ) -> PlayerAgent:
        if not players:
            raise ValueError("No players provided to collect_votes")

        vote_mp: dict[str, int] = {player.name: 0 for player in players}
        valid_names = set(vote_mp.keys())

        if role == Role.MAFIA:
            prompt = "Who do you vote to kill?"
        elif role == Role.HEALER:
            prompt = "Who do you vote to heal?"
        elif role == Role.DETECTIVE:
            prompt = "Who do you vote to check?"
        else:
            prompt = "Who do you vote to eliminate?"

        choices_block = "\n".join(valid_names)
        instruction = (
            "\nChoose exactly ONE name from the list above.\n"
            "Strictly return the full and correct name only."
        )

        for player in players:
            proposals_text = "\n".join(proposals)
            raw = str(
                player.speak(
                    f"{prompt}\nAmongst: {choices_block}.\n"
                    f"As per the following proposals:\n{proposals_text}\n"
                    f"{instruction}"
                )
            ).strip()

            normalized = self._normalize_name(raw)

            # Fast path: exact match
            if normalized in valid_names:
                vote_mp[normalized] += 1
                continue

            # Fallback: substring / loose match (handles extra text)
            matched = None
            for name in valid_names:
                if name in normalized:
                    matched = name
                    break

            if matched:
                vote_mp[matched] += 1
            else:
                # Hard fallback: abstain or random valid vote
                # (random keeps the game moving; abstain biases less)
                fallback = random.choice(tuple(valid_names))
                vote_mp[fallback] += 1

        # Determine winner
        max_votes = max(vote_mp.values())
        top_candidates = [
            name for name, count in vote_mp.items() if count == max_votes
        ]

        # Deterministic tie-break (stable + reproducible)
        winner_name = sorted(top_candidates)[0]

        for player in players:
            if player.name == winner_name:
                return player

        # This should never happen, but be defensive
        raise RuntimeError("Winner could not be resolved from vote map")
