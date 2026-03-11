from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from model import (
    ChatModel,
    GenerateOptions,
    Message,
    ModelResponse,
    ModelResponseChunk,
    ModelRegistry,
    SUPPORTED_MODELS,
    get_dummy_model,
)
from enum import Enum

_DEFAULT_SYSTEM_PROMPT_RETRIEVE = ""
_DEFAULT_SYSTEM_PROMPT_CREATIVE = ""

# TODO: remove
registry = ModelRegistry(SUPPORTED_MODELS)


class RagMode(Enum):
    RETRIEVE = 1
    CREATIVE = 2


@dataclass
class MessageData:
    user_prompt: str
    tim_context: str
    chat_history: list[Message]
    mode: RagMode
    max_tokens: int


class Rag:
    mode: list[RagMode]
    # TODO:
    # Need reference to PluginCore/indexer/database
    # or callbacks to functions to get context, user chat history

    def __init__(
        self,
        model_spec: ModelRegistry.ModelSpec | None = None,
    ):
        # TODO: modify model creation
        # Joko kaikki tuetut modelit tallennetaan muistiin modelistaan tai sitten luodaan vain tarvittaessa?
        self.model = registry.create(model_spec) if model_spec else get_dummy_model()

    def answer(self, request_data: MessageData) -> Iterable[ModelResponseChunk]:
        """Give an answer to the user using the model."""
        messages = self.build_prompt()
        # TODO: simplify?
        try:
            if self.model.get_info().supports_streaming:
                return self.model.generate_stream(messages, GenerateOptions())
            res: ModelResponse = self.model.generate(messages, GenerateOptions())
        except Exception as e:
            # TODO: better error handling
            print("error(RAG): ", str(e))
            return []
        # TODO: answer post processing
        # Include the urls/document ids?
        return [ModelResponseChunk(delta=res.content, usage=res.usage, done=True)]

    def build_prompt(self, message_data: MessageData) -> list[Message]:
        """Build the message list to send to the model."""
        mode: RagMode = message_data.mode
        system_msg: Message = self.system_message(mode)
        content: str = message_data.user_prompt
        history: list[Message] = message_data.chat_history
        context: str = message_data.tim_context
        context_msg: Message = Message(
            # TODO: change role?
            role="user",
            content=f"<CONTEXT> {context} </CONTEXT>",
        )
        user_msg: Message = Message(role="user", content=content)
        prompt: list[Message] = [system_msg]
        prompt.extend(history)
        prompt.append(context_msg)
        prompt.append(user_msg)
        return prompt

    def system_message(self, mode: RagMode) -> Message:
        """Initialize the system message."""
        # TODO: optimize
        if mode == RagMode.RETRIEVE:
            msg = _DEFAULT_SYSTEM_PROMPT_RETRIEVE
        elif mode == RagMode.CREATIVE:
            msg = _DEFAULT_SYSTEM_PROMPT_CREATIVE
        else:
            msg = ""
        return Message(role="system", content=msg)
