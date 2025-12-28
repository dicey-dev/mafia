import random

from agents.god import GodAgent
from agents.player import PlayerAgent
from game.types import Role
from utils.memory import summarize_round


class MafiaGame:
    def __init__(self, god: GodAgent, players: list[PlayerAgent]) -> None:
        self.god = god
        self.players = players
        self.alive_players = players[:]
        self.round_no = 0
        self.summary = ""
        self.logs: list[str] = []
        self.user_instruction: str = ""

    def assign_roles(self) -> None:
        random.shuffle(self.players)
        roles = (
            [Role.MAFIA] * 2
            + [Role.DETECTIVE] * 2
            + [Role.HEALER]
            + [Role.VILLAGER] * (len(self.players) - 5)
        )
        for player, role in zip(self.players, roles):
            player.role = role
            # Reinitialize agent with role-specific tools
            player._initialize_agent()

    def reset_match(self) -> None:
        self.round_no, self.summary, self.logs = (0, "", [])

    def add_log(self, message: str):
        """Add log and sync to all alive players' memories.

        Args:
            message: Message to log (can already include [GOD]: or player prefix)
        """
        # If message doesn't start with a bracket, assume it's from god
        if not message.startswith("["):
            formatted_message = f"[GOD {self.god}]: {message}"
        else:
            formatted_message = message

        print(formatted_message)
        self.logs.append(formatted_message)
        # Sync to all alive players
        for player in self.alive_players:
            player.add_public_log(formatted_message)

    def get_user_instruction(self) -> str:
        """Get special instruction from user via stdin.

        Returns:
            User instruction string
        """
        print(f"\n[GOD {self.god}]: Do you have any special instructions for this round?")
        print("(Press Enter for none, or type your instruction):")
        try:
            instruction = input().strip()
            return instruction
        except (EOFError, KeyboardInterrupt):
            return ""

    def discuss(self, role: Role, players: list[PlayerAgent]) -> str:
        """Handle discussion phase for a specific role.

        Args:
            role: The role discussing
            players: List of players with this role

        Returns:
            Name of selected target player
        """
        if not players:
            return ""

        other_alive = [
            p.name
            for p in self.alive_players
            if p.name in [pp.name for pp in self.alive_players]
        ]

        if role == Role.MAFIA:
            proposal_prompt = (
                "You are mafia. Discuss with other mafias who to kill. "
                "Use propose_kill tool to suggest a target. "
                f"Available targets: {', '.join(other_alive)}"
            )
        elif role == Role.HEALER:
            proposal_prompt = (
                "You are the healer. Choose who to heal. "
                f"Available targets: {', '.join(other_alive)}"
            )
        elif role == Role.DETECTIVE:
            proposal_prompt = (
                "You are detectives. Discuss who to investigate. "
                "Use suspect_player tool to suggest a target. "
                f"Available targets: {', '.join(other_alive)}"
            )
        else:
            # Day discussion
            proposal_prompt = (
                "Discuss your thoughts, raise suspicion, point "
                "out anomalous behaviour of others. If you're the mafia, "
                "try to deceive. Use accuse_player to accuse, defend_self "
                "to defend. These players are still alive: "
                f"{', '.join([p.name for p in self.alive_players])}"
            )

        proposals = []
        for p in players:
            # Sync latest logs before discussion
            p.sync_logs(self.logs)
            response = p.speak(proposal_prompt, use_tools=True)
            proposal_msg = f"[{p.name}]: {response}"
            proposals.append(proposal_msg)
            if role == Role.ALL:
                self.add_log(proposal_msg)

        # Collect votes using round-robin format
        target = self.collect_votes_round_robin(role, players, proposals)
        return target.name

    def collect_votes_round_robin(
        self, role: Role, players: list[PlayerAgent], proposals: list[str]
    ) -> PlayerAgent:
        """Collect votes in round-robin format matching README.

        Args:
            role: The role voting
            players: List of players voting
            proposals: Previous proposals/discussion

        Returns:
            Selected player
        """
        if not players:
            raise ValueError("No players provided to collect_votes")

        # Valid targets are all alive players (can vote for anyone alive)
        all_alive_names = [p.name for p in self.alive_players]
        valid_names = set(all_alive_names)
        # Initialize vote map with all alive players
        vote_mp: dict[str, int] = {name: 0 for name in all_alive_names}

        if role == Role.MAFIA:
            prompt_base = "Who do you vote to kill?"
        elif role == Role.HEALER:
            prompt_base = "Who do you vote to heal?"
        elif role == Role.DETECTIVE:
            prompt_base = "Who do you vote to check?"
        else:
            prompt_base = "Who do you vote to eliminate?"

        # Round-robin voting
        for player in players:
            # Sync logs before voting
            player.sync_logs(self.logs)
            self.add_log(f"{player.name}")
            choices_block = "\n".join(sorted(valid_names))
            instruction = (
                f"{prompt_base}\nAmongst: {choices_block}.\n"
                f"Proposals from discussion:\n{chr(10).join(proposals)}\n"
                "Choose exactly ONE name from the list above. "
                "Use vote_for_player tool or return the name directly."
            )
            raw = player.speak(instruction, use_tools=True).strip()
            normalized = self.god._normalize_name(raw)

            # Extract player name from response
            matched = None
            # Check for exact match
            if normalized in valid_names:
                matched = normalized
            else:
                # Check for substring match
                for name in valid_names:
                    if name.lower() in normalized.lower():
                        matched = name
                        break

            if matched:
                vote_mp[matched] += 1
                vote_msg = f"[{player.name}]: I vote for {matched}"
            else:
                # Fallback
                fallback = random.choice(tuple(valid_names))
                vote_mp[fallback] += 1
                vote_msg = f"[{player.name}]: I vote for {fallback} (fallback)"

            self.add_log(vote_msg)

        # Determine winner
        max_votes = max(vote_mp.values())
        top_candidates = [
            name for name, count in vote_mp.items() if count == max_votes
        ]
        winner_name = sorted(top_candidates)[0]

        for player in self.alive_players:
            if player.name == winner_name:
                return player

        raise RuntimeError("Winner could not be resolved from vote map")

    def match_start(self) -> None:
        """Start the mafia game match."""
        self.assign_roles()

        while True:
            self.round_no += 1
            print(f"\n{'*' * 20} ROUND {self.round_no} {'*' * 20}")

            # Night phase
            self.add_log("City goes to sleep")

            # Mafia phase
            self.add_log("Mafias wake up, who you want to kill?")
            mafia_players = [
                p for p in self.alive_players if p.role == Role.MAFIA
            ]
            if mafia_players:
                to_kill = self.discuss(role=Role.MAFIA, players=mafia_players)
            else:
                to_kill = ""
            self.add_log("Mafias go to sleep")

            # Healer phase
            self.add_log("Healers wake up, who you want to heal?")
            healer_players = [
                p for p in self.alive_players if p.role == Role.HEALER
            ]
            if healer_players:
                to_heal = self.discuss(
                    role=Role.HEALER, players=healer_players
                )
            else:
                to_heal = ""

            self.add_log("Healers go to sleep")

            # Detective phase
            self.add_log("Detectives wake up. Who do you suspect?")
            detective_players = [
                p for p in self.alive_players if p.role == Role.DETECTIVE
            ]
            if detective_players:
                to_check_name = self.discuss(
                    role=Role.DETECTIVE, players=detective_players
                )
                # Find the player object
                to_check_player = next(
                    (
                        player
                        for player in self.alive_players
                        if player.name == to_check_name
                    ),
                    None,
                )
                if to_check_player:
                    is_mafia = to_check_player.role == Role.MAFIA
                    reveal_msg = (
                        f"{to_check_player.name} is "
                        f"{'' if is_mafia else 'not '}a mafia."
                    )
                    # Private reveal to detectives only
                    for detective in detective_players:
                        detective.add_private_log(f"[GOD]: {reveal_msg}")
                    self.add_log(
                        f"Yes {to_check_player.name} is {'a mafia' if is_mafia else 'not a mafia'}"
                    )
            else:
                to_check_player = None

            self.add_log("Detectives go to sleep")

            # User instruction phase
            self.user_instruction = self.get_user_instruction()
            if self.user_instruction:
                self.add_log(
                    f"Special instruction received: {self.user_instruction}"
                )
                # Let god process the instruction
                god_response = self.god.decide(
                    f"Special instruction: {self.user_instruction}. "
                    "Acknowledge and explain how you will follow it."
                )
                self.add_log(f"God acknowledges: {god_response}")

            # Day phase
            self.add_log(
                f"City wakes up, finding {'no one' if to_kill == to_heal else to_kill} dead."
            )
            # Remove killed player if not healed
            if to_kill and to_kill != to_heal:
                self.alive_players = [
                    player
                    for player in self.alive_players
                    if player.name != to_kill
                ]
                # Mark as dead
                killed_player = next(
                    (p for p in self.players if p.name == to_kill), None
                )
                if killed_player:
                    killed_player.alive = False

            # Day discussion
            self.add_log("Discussion begins. Share suspicions and defend.")
            to_eliminate_name = self.discuss(
                role=Role.ALL, players=self.alive_players
            )

            # Voting phase
            self.add_log("Voting begins.")
            to_eliminate = next(
                (
                    player
                    for player in self.alive_players
                    if player.name == to_eliminate_name
                ),
                None,
            )

            if to_eliminate:
                if to_eliminate.role == Role.MAFIA:
                    self.add_log(
                        f"A Mafia ({to_eliminate.name}) has been eliminated."
                    )
                else:
                    self.add_log(
                        f"{to_eliminate.name} has been voted out and he was not a mafia."
                    )
                # Remove eliminated player
                self.alive_players = [
                    p
                    for p in self.alive_players
                    if p.name != to_eliminate.name
                ]
                to_eliminate.alive = False

            self.summary = summarize_round(self.god.llm, self.logs)
            print(f"\n{'*' * 20} ROUND {self.round_no} ENDS {'*' * 20}\n")

            # Check win conditions
            mafia_alive = [
                p for p in self.alive_players if p.role == Role.MAFIA
            ]
            town_alive = [
                p for p in self.alive_players if p.role != Role.MAFIA
            ]

            if not mafia_alive:
                print("Villagers win!")
                break
            if len(mafia_alive) >= len(town_alive):
                print("Mafia wins!")
                break
