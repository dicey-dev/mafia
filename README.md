Rough Game idea

```python
class MafiaGame:
    def __init__(self, god, players: list) -> None:
        # god can be langchain model of langraph model
        self.god = god
        # players will be a list of langchain models with different personalities
        self.players = players
        # when a new game is initiallized, all players are alive
        self.alive_players = players

        # at the start of a players will be randomly assigned roles as per the proportions mentioned below and populated in their respoective buckets
        self.mafias = []
        self.villagers = []
        self.healers = []
        self.detectives = []

    def match_start(self):
        # god assigns roles to each player in the following proportion
        # 10 players -> 2 mafia + 2 detectives + 1 healers + 5 villagers

        # match begins here
        while len(self.villagers) + len(self.healers) + len(
            self.detectives
        ) > len(self.mafias) or len(self.mafias):
            # New round begins, where each round will go as such
            # god announces -> Villagers go to sleep
            # wakes up the mafia:
            #   if more than one mafia is alive then they have a quick discussion on who to eliminate and picks up the target
            #   mafias have to make up a consensus on who to kill within 1 min
            # then god sleeps the mafias
            #
            # god wakes up the healer
            #   healer chooses who to heal within 1 min
            # then god puts healer to sleep
            #
            # god wakes up the detectives
            #   detectives makes up the concensus about who should they query for to the god in 1 min
            #   Asks god if the suspected one is mafia or not to which god answers only to them
            # then god puts detectives to sleep
            #
            # then god asks for an input from the terminal from me which it'll take from stdin where,
            # I might have special instrution for god for the next round
            #
            # god must abide by my instructions
            # then god wakes up the city
            # then discussion between alive_players start which includes villagers + healers + detectives + mafias

            # NOTE: All of god's announcements and discussions should be printed on the terminal as following:
            # *****************ROUND-#<NUMBER>*****************
            # [GOD]: City goes to sleep
            # [GOD]: Mafias wake up, who you want to kill?
            # [Mafia 1]: we should kill <Player#_>
            # [Mafia 2]: no we should kill <Player#_>
            # [GOD]: What's your final choice?
            # [Mafia 1]: <Player#_>
            # [GOD]: <Mafia #2>?
            # [Mafia 2]: I agree.
            # [GOD]: Mafias go to sleep.
            # [GOD]: Healers wake up, who you want to heal?
            # [Healer 1]: I want to heal <Player#_>
            # [GOD]: Healers go to sleep.
            # [GOD]: Detetives wake up. Who do you suspect?
            # [Detective 1]: I want to check for <Player#_>
            # [Detective 2]: Same
            # [GOD]: Yes <Player #_> is a mafia
            # [GOD]: Detectives go to sleep.
            # [GOD]: City wakes up, finding {<Player #_> dead} or {no one dead}
            # A timer of 5 mins start before voting begins
            # City haves a discussion on suspisions and argues over defenses,
            # here LLM agents active as players should get creative and try to deceiving as much as possible.
            # Voting can begin if a concensus is there or timer is up but at the end of the it's upto me to decide
            # when voting begins so god should prompt me if I want the discussion to continue or should voting be
            # started.
            # God goes rouund robin to every alive player to collect votes which should be printed as following
            # [GOD]: <Player #1>
            # [Player #1]: I vote for <Player #2>
            # [Player #2]: I vote for <Player #6>
            # ...
            #
            # Player with the max votes is eliminated
            #
            # God asks me for special per round instruction
            # God abides by my instruction
            # *****************ROUND-#<NUMBER> ENDS*****************
            #
            # Subsequent rounds begin
            pass

        print("Mafia Wins!!" if self.mafias else "Villagers Lives!!")
        # roles reset after the match
        (
            self.alive_players,
            self.mafias,
            self.healers,
            self.villagers,
            self.detectives,
        ) = self.players, [], [], [], []
```
