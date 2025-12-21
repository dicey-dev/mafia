from langchain.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI


def summarize_round(
    llm: ChatGoogleGenerativeAI,
    round_logs: list[str],
) -> str:
    messages = [
        SystemMessage(content="Summarize the Mafia round concisely."),
        HumanMessage(content="\n".join(round_logs)),
    ]
    return str(llm.invoke(messages).content)


def summarize_memory(llm: ChatGoogleGenerativeAI, memory: list[str]) -> str:
    messages = [
        SystemMessage(content="Summarize these memory logs"),
        HumanMessage(content="\n".join(memory)),
    ]
    return str(llm.invoke(messages).content)
