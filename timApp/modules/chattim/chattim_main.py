import os
from dataclasses import dataclass
from typing import Any
from flask import request, Response
from timApp.modules.chattim.plugincore import PluginCore

from timApp.document.document import Document
from timApp.modules.chattim.database_handler import TimDatabase
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

_plugincore = PluginCore()


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


@dataclass(frozen=True)
class PluginChatAnswer:
    response: str
    error: str


@chattim.post("/ask")
def define_ask_route() -> Response:
    # TODO: pitäisi varmaan muuttaa jotenkin tyyliin: define_ask_route(input: SomeDataClass) jne
    data = request.get_json()
    user_input = data.get("input")
    user_id = data.get("user_id")
    document_id = data.get("document_id")
    conversation_id = data.get("conversation_id")

    resp = _plugincore.chat_request(user_id, document_id, conversation_id, user_input)
    returnable = {"web": {"result": resp.value, "error": resp.error}}

    return json_response(returnable)


@chattim.post("/create_instance")
def define_create_instance() -> Response:
    data = request.get_json()
    user_id = data.get("user_id")
    document_id = data.get("document_id")

    _plugincore.create_instance(user_id, document_id)

    web: PluginAnswerWeb = {"result": "Instance created"}
    result: PluginAnswerResp = {"web": web}

    return json_response(result)
