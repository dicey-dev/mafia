from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from game.types import Role
from utils.memory import summarize_memory


class PlayerAgent(BaseModel):
    name: str
    role: Role | None = None
    alive: bool = True
    system_prompt: str
    llm: ChatGoogleGenerativeAI
    memory: list[str] = []

    def speak(self, prompt: str) -> str:
        messages = [
            SystemMessage(content=self.system_prompt),
            # HumanMessage(
            #     content=f"Here's what I can I recall: {summarize_memory(self.llm, self.memory)}"
            # ),
            *[HumanMessage(content=m) for m in self.memory],
            HumanMessage(content=prompt),
        ]
        response = str(self.llm.invoke(messages).content).strip()
        self.memory.append(response)
        return response
