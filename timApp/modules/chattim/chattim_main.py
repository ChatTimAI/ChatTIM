from dataclasses import dataclass
from typing import Any

from tim_common.markupmodels import GenericMarkupModel
from tim_common.pluginserver_flask import (
    GenericHtmlModel,
    GenericAnswerModel,
    register_plugin_app,
    launch_if_main,
    PluginAnswerResp,
    PluginReqs,
    EditorTab,
    PluginAnswerWeb,
)
import os
from rag import *
from model import *


@dataclass
class ChatTimMarkupModel(GenericMarkupModel):
    pass


# TODO: make proper dataclasses
ChatTimInputModel = dict[str, Any]
ChatTimStateModel = dict[str, Any]


@dataclass
class ChatTimHtmlModel(
    GenericHtmlModel[ChatTimInputModel, ChatTimMarkupModel, ChatTimStateModel]
):
    def get_component_html_name(self) -> str:
        return "chattim-runner"


@dataclass
class ChatTimAnswerModel(
    GenericAnswerModel[ChatTimInputModel, ChatTimMarkupModel, ChatTimStateModel]
):
    pass


def answer(_args: ChatTimAnswerModel) -> PluginAnswerResp:
    web: PluginAnswerWeb = {}
    result: PluginAnswerResp = {"web": web}
    user_input = _args.input["userinput"]

    model_info = SUPPORTED_MODELS.get("openai")[0]
    try:
        api_key = os.getenv("OPENAI_API_KEY")
    except ValueError as e:
        print("Failed to get api_key: ", str(e))
        web["result"] = "Failed to get api_key: " + str(e)
        return result

    spec = ModelRegistry.ModelSpec(
        provider=model_info.provider,
        model_id=model_info.model_id,
        api_key=api_key,
    )

    rag: Rag = Rag(model_spec=spec)
    prompt: UserPrompt = UserPrompt(user_id="", content=user_input)

    answer_msg = ""
    usage = None
    stream = rag.answer(prompt)
    for msg in stream:
        answer_msg += msg.delta or ""
        if msg.usage is not None:
            usage = msg.usage
        print(msg)
    print("Usage:", usage)

    web["result"] = answer_msg
    return result


def reqs() -> PluginReqs:
    templates = [
        """
``` {plugin="chattim" #taskidhere}
header: ChatTIM
```
""",
    ]
    editor_tabs: list[EditorTab] = [
        {
            "text": "Plugins",
            "items": [
                {
                    "text": "ChatTIM",
                    "items": [
                        {
                            "data": templates[0].strip(),
                            "text": "Chattim",
                            "expl": "Add a chatbot functionality",
                        },
                    ],
                },
            ],
        },
    ]
    result: PluginReqs = {
        "js": ["js/build/chattim.js"],
        "multihtml": True,
    }

    result["editor_tabs"] = editor_tabs
    return result


app = register_plugin_app(
    __name__,
    html_model=ChatTimHtmlModel,
    answer_model=ChatTimAnswerModel,
    answer_handler=answer,
    reqs_handler=reqs,
)


launch_if_main(__name__, app)
