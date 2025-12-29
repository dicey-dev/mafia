"""Tool definitions for Mafia game agents."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class VoteInput(BaseModel):
    """Input for voting on a player."""

    player_name: str = Field(description="Name of the player to vote for")


class ProposeKillInput(BaseModel):
    """Input for mafia kill proposal."""

    target: str = Field(description="Name of the player to kill")


class ProposeHealInput(BaseModel):
    """Input for healer action."""

    target: str = Field(description="Name of the player to heal")


class SuspectPlayerInput(BaseModel):
    """Input for detective investigation."""

    target: str = Field(description="Name of the player to investigate")


class AccusePlayerInput(BaseModel):
    """Input for public accusation."""

    target: str = Field(description="Name of the player to accuse")
    reason: str = Field(description="Reason for the accusation")


class DefendSelfInput(BaseModel):
    """Input for defense statement."""

    statement: str = Field(description="Your defense statement")


@tool("vote_for_player", args_schema=VoteInput)
def vote_for_player(player_name: str) -> str:
    """Vote for a player during voting phase.

    IMPORTANT: Use this tool when you need to cast your vote. Do NOT just say "I vote for X" in text.
    You MUST call this tool with the player's name to register your vote.

    Args:
        player_name: Name of the player to vote for (must be an exact match from available players)

    Returns:
        Confirmation message
    """
    return f"I vote for {player_name}"


@tool("propose_kill", args_schema=ProposeKillInput)
def propose_kill(target: str) -> str:
    """Propose a kill target as mafia.

    IMPORTANT: Use this tool when discussing who to kill with other mafias.
    Do NOT just say "I propose we kill X" in text. You MUST call this tool to make your proposal.

    Args:
        target: Name of the player to kill (must be an exact match from available players)

    Returns:
        Proposal message
    """
    return f"I propose we kill {target}"


@tool("propose_heal", args_schema=ProposeHealInput)
def propose_heal(target: str) -> str:
    """Propose a heal target as healer.

    IMPORTANT: Use this tool when choosing who to heal.
    Do NOT just say "I want to heal X" in text. You MUST call this tool to make your choice.

    Args:
        target: Name of the player to heal (must be an exact match from available players)

    Returns:
        Proposal message
    """
    return f"I want to heal {target}"


@tool("suspect_player", args_schema=SuspectPlayerInput)
def suspect_player(target: str) -> str:
    """Suspect a player for investigation as detective.

    IMPORTANT: Use this tool when discussing who to investigate with other detectives.
    Do NOT just say "I suspect X" in text. You MUST call this tool to make your suggestion.

    Args:
        target: Name of the player to investigate (must be an exact match from available players)

    Returns:
        Suspicion message
    """
    return f"I suspect {target}"


@tool("accuse_player", args_schema=AccusePlayerInput)
def accuse_player(target: str, reason: str) -> str:
    """Publicly accuse a player during discussion.

    IMPORTANT: Use this tool when you want to publicly accuse someone during day discussion.
    Do NOT just say "I accuse X because Y" in text. You MUST call this tool to make your accusation.
    This tool will format your accusation properly for public discussion.

    Args:
        target: Name of the player to accuse (must be an exact match from available players)
        reason: Clear reason for the accusation (explain why you suspect them)

    Returns:
        Accusation message
    """
    return f"I accuse {target} because {reason}"


@tool("defend_self", args_schema=DefendSelfInput)
def defend_self(statement: str) -> str:
    """Defend yourself against accusations.

    IMPORTANT: Use this tool when you need to defend yourself against accusations.
    Do NOT just say "Let me defend myself" in text. You MUST call this tool with your defense statement.
    This tool will format your defense properly for public discussion.

    Args:
        statement: Your defense statement (explain why the accusations are wrong)

    Returns:
        Defense message
    """
    return f"Let me defend myself: {statement}"


# God tools
class PrivateRevealInput(BaseModel):
    """Input for private detective reveal."""

    player_name: str = Field(description="Name of investigated player")
    is_mafia: bool = Field(description="Whether the player is mafia")


@tool("private_reveal", args_schema=PrivateRevealInput)
def private_reveal(player_name: str, is_mafia: bool) -> str:
    """Privately reveal investigation result to detective.

    Args:
        player_name: Name of investigated player
        is_mafia: Whether the player is mafia

    Returns:
        Reveal message
    """
    status = "is" if is_mafia else "is not"
    return f"{player_name} {status} a mafia"


@tool("get_special_instruction")
def get_special_instruction() -> str:
    """Get special instruction from user via stdin.

    Use this tool when you need special instructions from the user
    to make an announcement or decision.
    The tool will block waiting for user input.
    """
    print("\n[GOD]: Do you have any special instructions for this round?")
    print("(Press Enter for none, or type your instruction):")
    try:
        instruction = input().strip()
        return instruction
    except (EOFError, KeyboardInterrupt):
        return ""


@tool("exit_game")
def exit_game() -> None:
    """Exit the game immediately.

    WARNING: This tool should ONLY be used when explicitly instructed
    by the user via special_instruction. Do NOT use this tool under
    any other circumstances. Using this tool will terminate the entire
    game program.
    """
    exit(1)


# Player tool list (roles get different subsets)
PLAYER_TOOLS = [vote_for_player, accuse_player, defend_self, suspect_player]

MAFIA_TOOLS = PLAYER_TOOLS + [propose_kill]

HEALER_TOOLS = PLAYER_TOOLS + [propose_heal]

DETECTIVE_TOOLS = PLAYER_TOOLS

# God tools
GOD_TOOLS = [
    private_reveal,
    exit_game,
    get_special_instruction,
]
