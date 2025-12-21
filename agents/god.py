import random
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.player import PlayerAgent
from game.types import Role


class GodAgent:
    def __init__(
        self, llm: ChatGoogleGenerativeAI, name: str, system_prompt: str
    ):
        self.llm = llm
        self.name = f"GOD [{name}]"
        self.system = SystemMessage(content=(system_prompt))

    def __str__(self) -> str:
        return self.name

    def decide(self, prompt: str) -> str:
        return str(
            self.llm.invoke(
                [self.system, HumanMessage(content=prompt)]
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
            raw = str(
                player.speak(
                    f"{prompt}\nAmongst: {choices_block}.\n As per the "
                    "following proposals,{'\n'.join(proposals)}\n{instruction}"
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
