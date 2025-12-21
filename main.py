from langchain_google_genai import ChatGoogleGenerativeAI

from agents.god import GodAgent
from agents.player import PlayerAgent
from game.mafia_game import MafiaGame
from utils.json_loader import load_personalities


def main():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=1.0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        # other params...
    )
    personalities = load_personalities("data/personalities.json")

    # Enter players who want to play here
    active_players = [
        "Joe Rogan",
        "Elon Musk",
        "Mahatma Gandhi",
        "Andrew Tate",
        "Diogenes",
        "Chael Sonnen",
        "Donald Trump",
        "Tony Stark",
        "Ultron",
        "JARVIS",
        "Lord Voldemort",
    ]
    players = [
        PlayerAgent(
            name=p["name"],
            system_prompt=p["prompt"],
            llm=llm,
        )
        for p in personalities
        if p["name"] in active_players
    ]

    # Enter your god here
    whos_god = "Albus Dumbledore"
    god_personality = next(
        (p for p in personalities if p["name"] == whos_god), None
    )
    if not god_personality:
        print("Oops! Got not found.")
        exit(1)

    god = GodAgent(
        llm=llm,
        name=god_personality["name"],
        system_prompt=god_personality["prompt"],
    )

    game = MafiaGame(god, players)
    game.match_start()


if __name__ == "__main__":
    main()
