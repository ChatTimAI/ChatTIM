from dataclasses import dataclass
from typing import Any, TypedDict

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
    PluginCustomResp,
    GenericCustomModel,
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


class ChatTIMAnswerWeb(PluginAnswerWeb):
    tokens: int


@dataclass
class ChatTimAnswerModel(
    GenericAnswerModel[ChatTimInputModel, ChatTimMarkupModel, ChatTimStateModel]
):
    pass


@dataclass
class ChatTimCustomModel(
    GenericCustomModel[ChatTimInputModel, ChatTimMarkupModel, ChatTimStateModel]
):
    pass


def answer(_args: ChatTimAnswerModel) -> PluginAnswerResp:
    web: ChatTIMAnswerWeb = {"tokens": 123}
    result: PluginAnswerResp = {"web": web}
    web[
        "result"
    ] = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."

    return result


def custom() -> PluginCustomResp:
    return {"base": {"custom": "nonsense"}}


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
    custom_model=ChatTimCustomModel,
    custom_handler=custom,
    reqs_handler=reqs,
)


launch_if_main(__name__, app)
