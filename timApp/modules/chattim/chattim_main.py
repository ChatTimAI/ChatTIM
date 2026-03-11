from __future__ import annotations
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
from flask import Response, request, stream_with_context
import os
import json
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

    model_info = SUPPORTED_MODELS["openai"][0]
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        web["result"] = "Missing OPENAI_API_KEY"
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


@app.post("/test")
def test():
    model_info = SUPPORTED_MODELS["openai"][0]
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return Response("Missing OPENAI_API_KEY\n", status=500, mimetype="text/plain")

    body_json = request.get_json(silent=True) or {}
    user_input = request.form.get("prompt") or body_json.get("prompt")
    if not user_input:
        return Response("Missing prompt\n", status=400, mimetype="text/plain")

    spec = ModelRegistry.ModelSpec(
        provider=model_info.provider,
        model_id=model_info.model_id,
        api_key=api_key,
    )

    rag: Rag = Rag(model_spec=spec)
    prompt: UserPrompt = UserPrompt(user_id="", content=user_input)

    @stream_with_context
    def generate() -> Any:
        stream = rag.answer(prompt)
        for msg in stream:
            if msg.delta:
                yield msg.delta
            if msg.usage:
                print(msg.usage)
                yield "\n\nUsage: " + str(msg.usage) + "\n"

    return Response(
        generate(),
        mimetype="text/plain",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


launch_if_main(__name__, app)
