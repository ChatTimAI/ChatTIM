from dataclasses import dataclass
from typing import Any
from google import genai

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


def answer(args: ChatTimAnswerModel) -> PluginAnswerResp:
    web: PluginAnswerWeb = {}
    result: PluginAnswerResp = {"web": web}
    prompt = args.input["userinput"]
    client = genai.Client()
    gemini_response = client.models.embed_content(
        model="gemini-embedding-001", contents=prompt
    )
    embedding: str = str(gemini_response.embeddings[0].values)
    web["result"] = f"Prompt:{prompt}, \nEmbedding:{embedding}"
    # web["result"] = embedding

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
