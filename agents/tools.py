"""Tool definitions for Mafia game agents."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from game.types import Role


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

    Args:
        player_name: Name of the player to vote for

    Returns:
        Confirmation message
    """
    return f"I vote for {player_name}"


@tool("propose_kill", args_schema=ProposeKillInput)
def propose_kill(target: str) -> str:
    """Propose a kill target as mafia.

    Args:
        target: Name of the player to kill

    Returns:
        Proposal message
    """
    return f"I propose we kill {target}"


@tool("propose_heal", args_schema=ProposeHealInput)
def propose_heal(target: str) -> str:
    """Propose a heal target as healer.

    Args:
        target: Name of the player to heal

    Returns:
        Proposal message
    """
    return f"I want to heal {target}"


@tool("suspect_player", args_schema=SuspectPlayerInput)
def suspect_player(target: str) -> str:
    """Suspect a player for investigation as detective.

    Args:
        target: Name of the player to investigate

    Returns:
        Suspicion message
    """
    return f"I suspect {target}"


@tool("accuse_player", args_schema=AccusePlayerInput)
def accuse_player(target: str, reason: str) -> str:
    """Publicly accuse a player during discussion.

    Args:
        target: Name of the player to accuse
        reason: Reason for the accusation

    Returns:
        Accusation message
    """
    return f"I accuse {target} because {reason}"


@tool("defend_self", args_schema=DefendSelfInput)
def defend_self(statement: str) -> str:
    """Defend yourself against accusations.

    Args:
        statement: Your defense statement

    Returns:
        Defense message
    """
    return f"Let me defend myself: {statement}"


# God tools
class AnnounceInput(BaseModel):
    """Input for god announcements."""

    message: str = Field(description="Message to announce")
    to_roles: list[Role] = Field(
        default=[], description="Roles to send message to (None = all)"
    )


class PrivateRevealInput(BaseModel):
    """Input for private detective reveal."""

    player_name: str = Field(description="Name of investigated player")
    is_mafia: bool = Field(description="Whether the player is mafia")


class ExecuteActionInput(BaseModel):
    """Input for executing night action."""

    action_type: str = Field(description="Type of action (kill, heal)")
    target: str = Field(description="Target player name")


@tool("announce", args_schema=AnnounceInput)
def announce(message: str, to_roles: list[Role] | None = None) -> str:
    """Announce a message as god.

    Args:
        message: Message to announce
        to_roles: Roles to send message to (None = all)

    Returns:
        Announcement confirmation
    """
    if to_roles:
        roles_str = ", ".join([r.value for r in to_roles])
        return f"Announcing to {roles_str}: {message}"
    return f"Announcing to all: {message}"


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


@tool("execute_night_action", args_schema=ExecuteActionInput)
def execute_night_action(action_type: str, target: str) -> str:
    """Execute a night action (kill or heal).

    Args:
        action_type: Type of action (kill, heal)
        target: Target player name

    Returns:
        Execution confirmation
    """
    return f"Executing {action_type} on {target}"


# Player tool list (roles get different subsets)
PLAYER_TOOLS = [
    vote_for_player,
    accuse_player,
    defend_self,
]

MAFIA_TOOLS = PLAYER_TOOLS + [propose_kill]

HEALER_TOOLS = PLAYER_TOOLS + [propose_heal]

DETECTIVE_TOOLS = PLAYER_TOOLS + [suspect_player]

# God tools
GOD_TOOLS = [announce, private_reveal, execute_night_action]
