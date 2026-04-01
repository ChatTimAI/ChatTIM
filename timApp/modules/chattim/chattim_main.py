import os
import json
from dataclasses import dataclass
from typing import Any, TypedDict
from flask import Response, stream_with_context
from webargs.flaskparser import use_args
from tim_common.marshmallow_dataclass import class_schema

from timApp.tim_app import csrf
from timApp.util.flask.responsehelper import json_response
from tim_common.markupmodels import GenericMarkupModel
from tim_common.pluginserver_flask import (
    GenericHtmlModel,
    PluginAnswerResp,
    PluginReqs,
    EditorTab,
    PluginAnswerWeb,
    create_nontask_blueprint,
)


@dataclass
class ChatTimMarkupModel(GenericMarkupModel):
    pass


# TODO: make proper dataclasses
ChatTimInputModel = dict[str, Any]
ChatTimStateModel = dict[str, Any]


class ChatTimAskResponse(TypedDict, total=False):
    answer: str | None
    usage: int | None


@dataclass
class ChatTimAskParams:
    input: str
    user_id: str
    document_id: int


@dataclass
class ChatTimHtmlModel(
    GenericHtmlModel[ChatTimInputModel, ChatTimMarkupModel, ChatTimStateModel]
):
    def get_component_html_name(self) -> str:
        return "chattim-runner"


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


chattim = create_nontask_blueprint(
    name=__name__,
    plugin_name="chattim",
    html_model=ChatTimHtmlModel,
    reqs_handler=reqs,
    csrf=csrf,
)


@chattim.post("/ask")
@use_args(class_schema(ChatTimAskParams)(), locations=("json",))
def define_ask_route(params: ChatTimAskParams):
    web: PluginAnswerWeb = {"result": "hello from server"}
    result: PluginAnswerResp = {"web": web}

    user_input = params.input
    user_id = params.user_id
    document_id = params.document_id

    # TODO: kytke plugincoreen

    return json_response(result)


from .model import ModelRegistry, SUPPORTED_MODELS, ModelSpec, Message, GenerateOptions

# TODO: temporary
reg = ModelRegistry(SUPPORTED_MODELS)
model = reg.create(
    ModelSpec(
        provider="openai",
        model_id="gpt-4.1-nano",
        api_key=os.getenv("OPENAI_API_KEY", ""),
    )
)


@chattim.post("/askStream")
@use_args(class_schema(ChatTimAskParams)(), locations=("json",))
def define_ask_stream_route(params: ChatTimAskParams):
    user_input = params.input

    def generate():
        # TODO: temporary, use the plugincore
        stream = model.generate_stream(
            [Message(role="user", content=user_input)], GenerateOptions()
        )
        for msg in stream:
            print(msg)
            if msg.delta:
                yield json.dumps(ChatTimAskResponse(answer=msg.delta)) + "\n"
            if msg.usage:
                yield json.dumps(
                    ChatTimAskResponse(usage=msg.usage.total_tokens)
                ) + "\n"

    return Response(
        stream_with_context(generate()),
        mimetype="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
