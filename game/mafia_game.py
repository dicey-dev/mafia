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
            [Role.MAFIA] * 2
            + [Role.DETECTIVE] * 2
            + [Role.HEALER]
            + [Role.VILLAGER] * (len(self.players) - 5)
        )
        for player, role in zip(self.players, roles):
            player.role = role

    def reset_match(self) -> None:
        self.round_no, self.round_summary, self.logs = (0, "", [])

    def add_log(self, message: str):
        print(message)
        self.logs.append(message)

    def discuss(self, role: Role, players: list[PlayerAgent]) -> str:
        if role == Role.MAFIA:
            proposal_prompt = "Choose to kill someone amongst: "
        elif role == Role.HEALER:
            proposal_prompt = "Choose to heal someone amongst: "
        elif role == Role.DETECTIVE:
            proposal_prompt = (
                "Who should we confirm as mafia from god amongst: "
            )
        else:
            proposal_prompt = (
                "Discuss your thoughts, raise suspicion, point "
                "out anamolous behaviour of others and if "
                "you're the mafia then try to decieve."
                " These players are still alive: "
            )
        proposals = []
        for p in players:
            proposals.append(
                f"{p.name: }"
                + p.speak(
                    proposal_prompt
                    + "\n".join([pp.name for pp in players if pp != p])
                    + " and me."
                )
            )
            if role == Role.ALL:
                self.add_log(proposals[-1])

        target = self.god.collect_votes(role, players, proposals)
        return target.name

    def match_start(self) -> None:
        self.assign_roles()

        while True:
            self.round_no += 1
            print(f"\n******** ROUND {self.round_no} ********")

            self.add_log(f"{self.god}: City goes to sleep")
            self.add_log(f"{self.god}: Mafia wakes up")
            to_kill = self.discuss(
                role=Role.MAFIA,
                players=[
                    p for p in self.alive_players if p.role == Role.MAFIA
                ],
            )
            self.add_log(f"{self.god}: Mafia goes to sleep")
            self.add_log(f"{self.god}: Healer wakes up")
            to_heal = self.discuss(
                role=Role.HEALER,
                players=[
                    p for p in self.alive_players if p.role == Role.HEALER
                ],
            )
            self.add_log(f"{self.god}: Healer goes to sleep")
            self.add_log(f"{self.god}: Detective wakes up")
            to_check = self.discuss(
                role=Role.DETECTIVE,
                players=[
                    p for p in self.alive_players if p.role == Role.DETECTIVE
                ],
            )

            for detective in filter(
                lambda x: x.role == Role.DETECTIVE, self.alive_players
            ):
                to_check = next(
                    player
                    for player in self.alive_players
                    if player.name == to_check
                )
                detective.memory.append(
                    f"{self.god}: {to_check} is {'not' if to_check.role != Role.MAFIA else ''} a mafia."
                )

            self.add_log(f"{self.god}: Detective goes to sleep")
            if to_kill != to_heal:
                self.alive_players = [
                    player
                    for player in self.alive_players
                    if player.name != to_kill
                ]
            self.add_log(
                f"{self.god}: City wakes up, finding {'no one' if to_kill == to_heal else to_kill} dead."
            )
            to_eliminate = self.discuss(
                role=Role.ALL, players=self.alive_players
            )
            to_eliminate = next(
                (
                    player
                    for player in self.alive_players
                    if player.name == to_eliminate
                ),
            )
            if to_eliminate.role == Role.MAFIA:
                self.add_log(f"{self.god}: A Mafia has been eliminated.")
            else:
                self.add_log(
                    f"{self.god}: {to_eliminate} has been voted out and he was not a mafia."
                )

            self.summary = summarize_round(self.god.llm, self.logs)

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
