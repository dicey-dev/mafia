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

    def assign_roles(self) -> None:
        random.shuffle(self.players)
        roles = (
            [Role.MAFIA] * 1
            + [Role.DETECTIVE] * 1
            + [Role.HEALER]
            + [Role.VILLAGER]
        )
        for player, role in zip(self.players, roles, strict=False):
            player.role = role
            # Reinitialize agent with role-specific tools
            player._initialize_agent()

    def reset_match(self) -> None:
        self.round_no, self.summary, self.logs, self.alive_players = (
            0,
            "",
            [],
            self.players[:],
        )

    def add_log(self, message: str):
        """Add public log and sync to all alive players' memories.

        Args:
            message: Message to log (can already include [GOD]: or
                player prefix)
        """
        # If message doesn't start with a bracket, assume it's from god
        self.logs.append(message)
        print(message)
        # Sync to all alive players
        for player in self.alive_players:
            player.memory.append(message)

    def add_private_log_to_role(self, role: Role, message: str):
        """Add private log to players with specific role and print.

        Args:
            role: The role to add the log to
            message: Message to log (role prefix will be added if not GOD)
        """
        # Print to terminal

        # Add to private logs of players with this role
        for player in self.alive_players:
            if player.role == role:
                player.memory.append(message)

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

        alive_player_names = [p.name for p in self.alive_players]

        if role == Role.MAFIA:
            proposal_prompt = (
                "You are mafia. Discuss with other mafias who to kill. "
                "IMPORTANT: When you want to suggest a target, you MUST use the propose_kill tool. "
                "Do NOT just say 'I propose we kill X' in text - you must call the propose_kill tool. "
                f"Available targets: {', '.join(alive_player_names)}"
            )
        elif role == Role.HEALER:
            proposal_prompt = (
                "You are the healer. Choose who to heal. "
                "IMPORTANT: When you want to choose a target to heal, you MUST use the propose_heal tool. "
                "Do NOT just say 'I want to heal X' in text - you must call the propose_heal tool. "
                f"Available targets: {', '.join(alive_player_names)}"
            )
        elif role == Role.DETECTIVE:
            proposal_prompt = (
                "You are detectives. Discuss who to investigate. "
                "IMPORTANT: When you want to suggest a target to investigate, you MUST use the suspect_player tool. "
                "Do NOT just say 'I suspect X' in text - you must call the suspect_player tool. "
                f"Available targets: {', '.join(alive_player_names)}"
            )
        else:
            # Day discussion
            proposal_prompt = (
                "Discuss your thoughts, raise suspicion, point "
                "out anomalous behaviour of others. If you're the mafia, "
                "try to deceive. "
                "IMPORTANT: When you want to accuse someone, you MUST use the accuse_player tool. "
                "When you need to defend yourself, you MUST use the defend_self tool. "
                "Do NOT just describe these actions in text - you must call the appropriate tools. "
                "These players are still alive: "
                f"{', '.join([p.name for p in self.alive_players])}"
            )

        proposals = []
        # Everyone gets to speak twice
        num_iterations = 2
        for iteration in range(num_iterations):
            for p in players:
                # Provide different context for second iteration
                if iteration == 0:
                    current_prompt = proposal_prompt
                else:
                    current_prompt = (
                        f"{proposal_prompt}\n"
                        "This is your second chance to speak. "
                        "Consider what others have said and provide additional thoughts or respond to their statements. "
                        "Do not simply repeat your previous statement."
                    )

                response = p.speak(current_prompt + "\n".join(proposals))
                # Extract clean response (remove player name prefix if present)
                clean_response = response
                if response.startswith(f"[{p.name}]:"):
                    clean_response = response.split(":", 1)[1].strip()

                # Skip if this is a duplicate of the last message from this player
                proposal_msg = f"[{p.name}]: {clean_response}"
                # Check if this is a duplicate of the last proposal from this player
                is_duplicate = False
                if proposals:
                    # Look backwards for the last message from this player
                    for prev_msg in reversed(proposals):
                        if prev_msg.startswith(f"[{p.name}]:"):
                            prev_content = (
                                prev_msg.split(":", 1)[1].strip()
                                if ":" in prev_msg
                                else prev_msg
                            )
                            if (
                                prev_content.strip().lower()
                                == clean_response.strip().lower()
                            ):
                                is_duplicate = True
                            break

                if not is_duplicate:
                    proposals.append(proposal_msg)
                    # Log discussions: private for role-specific,
                    # public for day discussion
                    if role == Role.ALL:
                        self.add_log(proposal_msg)
                    else:
                        self.add_private_log_to_role(role, proposal_msg)
                        print(proposal_msg)

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
            choices_block = "\n".join(sorted(valid_names))
            instruction = (
                f"{prompt_base}\nAmongst: {choices_block}.\n"
                f"Proposals from discussion:\n{'\n'.join(proposals)}\n"
                "IMPORTANT: You MUST use the vote_for_player tool to cast your vote. "
                "Do NOT just say 'I vote for X' in text - you must call the vote_for_player tool. "
                "Choose exactly ONE name from the list above."
            )
            print(f"[GOD {self.god}]: {player.name}, who do you wish to vote?")
            raw_response = player.speak(instruction).strip()

            # Extract player name from response
            # The vote_for_player tool returns "I vote for {player_name}"
            # But the response might not always follow this format
            vote_for = None
            prefix = "I vote for "
            if raw_response.startswith(prefix):
                vote_for = raw_response[len(prefix) :].strip()
            else:
                # If response doesn't start with prefix, treat entire response
                # as potential name
                vote_for = raw_response

            # Extract player name from response
            matched = None
            # Check for exact match
            if vote_for and vote_for in valid_names:
                matched = vote_for
            else:
                # Check for substring match
                if vote_for:
                    for name in valid_names:
                        if name.lower() in vote_for.lower():
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

            # Log votes: private for role-specific, public for day voting
            if role == Role.ALL:
                self.add_log(vote_msg)
            else:
                self.add_private_log_to_role(role, vote_msg)
                print(vote_msg)

        # Determine winner or loser however you look at it
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

            print(
                f"Mafias: {', '.join([p.name for p in self.alive_players if p.role == Role.MAFIA])}"
            )
            print(
                f"Healers: {', '.join([p.name for p in self.alive_players if p.role == Role.HEALER])}"
            )
            print(
                f"Detectives: {', '.join([p.name for p in self.alive_players if p.role == Role.DETECTIVE])}"
            )
            print(
                f"Villagers: {', '.join([p.name for p in self.alive_players if p.role == Role.VILLAGER])}"
            )

            print("*" * (40 + len(f" ROUND {self.round_no} ")))

            # Night phase
            self.add_log(f"[GOD {self.god}]: City goes to sleep")

            # Mafia phase
            self.add_log(
                f"[GOD {self.god}]: Mafias wake up, who you want to kill?"
            )
            mafia_players = [
                p for p in self.alive_players if p.role == Role.MAFIA
            ]
            to_kill = self.discuss(role=Role.MAFIA, players=mafia_players)
            self.add_log(f"[GOD {self.god}]: Mafias go to sleep")

            # Healer phase
            self.add_log(
                f"[GOD {self.god}]: Healers wake up, who you want to heal?"
            )
            healer_players = [
                p for p in self.alive_players if p.role == Role.HEALER
            ]
            to_heal = self.discuss(role=Role.HEALER, players=healer_players)

            self.add_log(f"[GOD {self.god}]: Healers go to sleep")

            # Detective phase
            self.add_log(
                f"[GOD {self.god}]: Detectives wake up, who do you suspect?"
            )
            detective_players = [
                p for p in self.alive_players if p.role == Role.DETECTIVE
            ]
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
                # Private reveal to detectives only - use role-based
                # private log
                self.add_private_log_to_role(
                    Role.DETECTIVE, f"[GOD {self.god}]: {reveal_msg}"
                )
                print(f"[GOD {self.god}]: {reveal_msg}")

            self.add_log(f"[GOD {self.god}]: Detectives go to sleep")

            # Day phase
            death_msg = "no one" if to_kill == to_heal else to_kill
            self.add_log(
                f"[GOD {self.god}]: City wakes up, finding {death_msg} dead."
            )
            # Remove killed player if not healed
            if to_kill and to_kill != to_heal:
                self.alive_players = [
                    player
                    for player in self.alive_players
                    if player.name != to_kill
                ]

            # Day discussion
            to_eliminate_name = self.discuss(
                role=Role.ALL, players=self.alive_players
            )

            to_eliminate = next(
                (
                    player
                    for player in self.alive_players
                    if player.name == to_eliminate_name
                ),
                None,
            )

            if to_eliminate:
                prompt = (
                    f"The voting has concluded and {to_eliminate.name} "
                    f"has been voted to be eliminated. "
                    f"Since this is time to make the last announcement "
                    f"of the round related to elimination, use "
                    f"get_special_instruction tool to get instruction "
                    f"from the user about how announcement should be like"
                )
                god_announcement = self.god.decide(prompt)
                self.add_log(god_announcement)
                # Remove eliminated player
                self.alive_players = [
                    p
                    for p in self.alive_players
                    if p.name != to_eliminate.name
                ]

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
        self.reset_match()
