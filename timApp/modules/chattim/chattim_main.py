import os
import json
from dataclasses import dataclass
from typing import Any, TypedDict
from flask import request, Response, stream_with_context

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
def define_ask_route():
    web: PluginAnswerWeb = {"result": "hello from server"}
    result: PluginAnswerResp = {"web": web}

    # TODO: pitäisi varmaan muuttaa jotenkin tyyliin: define_ask_route(input: SomeDataClass) jne
    data = request.get_json()
    user_input = data.get("input")
    user_id = data.get("user_id")
    document_id = data.get("document_id")

    # TODO: kytke plugincoreen

    return json_response(result)


class ChatTimAskResponse(TypedDict):
    data: str | None
    usage: int | None


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
def define_ask_stream_route():
    data = request.get_json()
    user_input = data.get("input")
    user_id = data.get("user_id")
    document_id = data.get("document_id")

    def generate():
        # TODO: temporary, use the plugincore
        stream = model.generate_stream(
            [Message(role="user", content=user_input)], GenerateOptions()
        )
        for msg in stream:
            print(msg)
            if msg.delta:
                yield json.dumps(ChatTimAskResponse(data=msg.delta, usage=None)) + "\n"
            if msg.usage:
                yield json.dumps(
                    ChatTimAskResponse(data=None, usage=msg.usage.total_tokens)
                ) + "\n"

    return Response(
        stream_with_context(generate()),
        mimetype="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
