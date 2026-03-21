import os
import time
from enum import Enum
from dataclasses import dataclass
from timApp.modules.chattim.rag import (
    Rag,
    MessageData,
    RagMode,
    ModelSpec,
    Message,
    Iterable,
)
from typing import Generic, TypeVar

from timApp.modules.chattim.model import ModelResponseChunk, Usage
from timApp.modules.chattim.conversation import ConversationManager, ChatMessage

T = TypeVar("T")
E = TypeVar("E")


class Result(Generic[T, E]):
    def __init__(self, value: T | None = None, error: E | None = None):
        if (value is None) == (error is None):
            raise ValueError("Provide exactly one of value or error")
        self.value: T | None = value
        self.error: E | None = error

    def ok(self) -> bool:
        return self.error is None

    def __repr__(self):
        return f"Ok({self.value})" if self.ok() else f"Err({self.error})"


# Nämä pitää siirtää myöhemmin jonnekkin muualle
@dataclass
class GlobalPolicy:
    pass


@dataclass
class StudentPolicy:
    pass


class PluginCore:
    rag: Rag = Rag()
    history_manager: ConversationManager = ConversationManager()

    # TODO: palautetaan token usage tätä kautta tai muualta?
    def chat_request(
        self, caller_id: str, document_id: int, conversation_id: int, user_input: str,
    ) -> Result[str | None, str | None]:
        if not self._instance_exists(document_id):
            return Result(error=f"No instance with id {document_id} exists")

        # policy check
        result: Result[str | None, str | None] = self._student_policy_check(
            caller_id, document_id
        )

        if not result.ok():
            return result

        timestamp_before = time.time_ns()
        plugin_id = str(document_id)
        history = self.history_manager.get_history(plugin_id, caller_id, str(conversation_id), 10)

        # TODO: fetch chat history
        chat_history: list[Message] = [Message(role=m.role, content=m.content) for m in history]
        # TODO: fetch mode for instance
        mode: RagMode = RagMode.RETRIEVE
        # TODO: how do we decide max tokens for request
        max_tokens_for_req = 99999

        msg_data = MessageData(
            user_prompt=user_input,
            context="",
            chat_history=chat_history,
            mode=mode,
            max_tokens=max_tokens_for_req,
        )
        iterable: Iterable[ModelResponseChunk] = self.rag.answer(
            msg_data,
            identifier=document_id,
        )

        whole_msg: str = ""
        usage: Usage | None = None
        for chunk in iterable:
            if chunk.delta:
                whole_msg += chunk.delta
            if chunk.usage:
                usage = chunk.usage

        # TODO: viestit arkistoidaan

        timestamp_after = time.time_ns()
        self.history_manager.append_messages(
            plugin_id,
            caller_id,
            str(conversation_id),
            [
                ChatMessage(role="user", content=user_input, usage=None, timestamp=timestamp_before),
                ChatMessage(role="assistant", content=whole_msg, usage=usage, timestamp=timestamp_after),
            ],
        )

        return Result(value=whole_msg, error=None)

    def create_instance(self, caller_id, document_id: int):
        # TODO: tarkista onko teacher jo tietokanssa, jos ei niin lisää
        # TODO: tarkista tässä oikeudet

        # TODO: tälle joku helpompi tapa vetää spec infosta tai jotain (tämä muutenkin väliaikainen)
        supp_models = self.rag.get_supported_models()
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key is not None:
            model = supp_models.get("openai")[0]
            spec = ModelSpec(
                provider=model.provider,
                model_id=model.model_id,
                api_key=openai_api_key,
            )
        else:
            model = supp_models.get("dummy")[0]
            spec = ModelSpec(
                provider=model.provider,
                model_id=model.model_id,
                api_key="dummy_api_key",
            )
        self.rag.add_model(spec, identifier=document_id)
        # TODO: lisää tietokantaan policyineen
        # TODO: indeksoinnit pyörimään

    def remove_instance(self, caller_id: str, document_id: int):
        pass

    def modify_instance_pages(
        self, caller_id: str, document_id: int, indexable_paths: list[str]
    ):
        pass

    def get_history(self, caller_id: str, document_id: int):
        pass

    def change_chatmode(self, caller_id: str, document_id: int, mode: RagMode):
        pass

    def set_globalpolicy(self, caller_id: str, document_id: int, policy: GlobalPolicy):
        pass

    def set_studentpolicy(
        self, caller_id: str, document_id: int, policy: StudentPolicy
    ):
        pass

    def _instance_exists(self, document_id) -> bool:
        # ideana todnäk pitää muistissa tiedetyt instanssi-idt jottei haeta aina tietokannalta turhaan
        # TODO: impl
        return True

    def _has_doc_modify_right(self, caller_id: str, document_id: int) -> bool:
        # TODO: impl
        return True

    def _student_policy_check(
        self, caller_id: str, document_id: int
    ) -> Result[str | None, str | None]:
        """
        Checks that user request is allowed as per set policies
        :param caller_id:  the user that is making the request
        :param document_id:  instance for the plugin
        :return: (can_make_req: bool, reason_for_deny: str)
        """
        # check userpolicy (if exists)
        # check globalpolicy
        # check against token usage estimate for the request if goes over the limit?
        # huom käyttäjälle pitäisi lähettää sitten varmaan joku ilmoitus että "menee x tokenia yli rajan"
        # TODO: impl
        return Result(value="ok", error=None)
