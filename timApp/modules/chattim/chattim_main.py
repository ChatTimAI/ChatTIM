from dataclasses import dataclass
from typing import Any

from timApp.timdb.sqa import db
from timApp.document.docentry import get_documents, DocEntry

from timApp.document.docentry import (
    DocEntry,
    get_documents_in_folder,
    get_documents,
)
from timApp.document.docinfo import DocInfo
from timApp.folder.folder import Folder
from timApp.item.deleting import (
    soft_delete_document,
)
from timApp.timdb.sqa import db, run_sql
from timApp.user.user import User
from timApp.user.usergroup import UserGroup
from timApp.user.users import get_rights_holders, remove_access
from timApp.user.userutils import grant_access


# import timApp.tim_app

import timApp.readmark.readparagraph  # ReadParagraph
import timApp.note.usernote  # UserNote
import timApp.auth.auth_models  # BlockAccess, etc.
import timApp.item.block  # Block
import timApp.messaging.messagelist.messagelist_models
import timApp.messaging.timMessage.internalmessage_models
import timApp.user.usergroup

import timApp.item.item
import timApp.user.user
import timApp.auth.get_user_rights_for_item

# from flask_migrate import Migrate


from timApp.defaultconfig import SQLALCHEMY_DATABASE_URI

# from timApp.testconfig import SQLALCHEMY_DATABASE_URI

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
from rag import Rag, UserPrompt
from model import (
    ChatModel,
    GenerateOptions,
    Message,
    ModelResponse,
    ModelResponseChunk,
    ModelRegistry,
    SUPPORTED_MODELS,
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


def answer(_args: ChatTimAnswerModel) -> PluginAnswerResp:
    web: PluginAnswerWeb = {}
    result: PluginAnswerResp = {"web": web}
    user_input = _args.input["userinput"]

    info = SUPPORTED_MODELS.get("openai")[0]
    try:
        api_key = os.getenv("OPENAI_API_KEY")
    except ValueError as e:
        print("Failed to get api_key: ", str(e))
        web["result"] = "Failed to get api_key: " + str(e)
        return result
    spec = ModelRegistry.ModelSpec(
        provider=info.provider,
        model_id=info.model_id,
        api_key=api_key,
    )

    rag: Rag = Rag(model_spec=spec)
    prompt: UserPrompt = UserPrompt(user_id="", content=user_input)

    answer_msg = ""
    stream = rag.answer(prompt)
    for msg in stream:
        answer_msg += msg.delta or ""
        print(msg)

    web["result"] = answer_msg

    get_documents(filter_folder="")
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

# if app.config["PROFILE"]:
# app.wsgi_app = ProfilerMiddleware(
#    app.wsgi_app,
#    sort_by=("cumtime",),
#    restrictions=[100],
#    profile_dir="/service/timApp/static/profiling",
# )


app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["DB_URI"] = SQLALCHEMY_DATABASE_URI
db.init_app(app)
db.app = app
# migrate = Migrate(app, db)

for var in [
    "DB_URI",
    "DEBUG",
    "MAIL_HOST",
    "PG_MAX_CONNECTIONS",
    "PLUGIN_CONNECT_TIMEOUT",
    "PROFILE",
    "SQLALCHEMY_MAX_OVERFLOW",
    "SQLALCHEMY_POOL_SIZE",
]:
    print(f'{var}: {app.config.get(var, "(undefined)")}')


launch_if_main(__name__, app)

# import os
# from sqlalchemy import create_engine, text
# from sqlalchemy.orm import sessionmaker
# db_name = os.getenv("COMPOSE_PROJECT_NAME", "tim")
# url = f"postgresql+psycopg2://postgres:postgresql@postgresql:5432/{db_name}"
# engine = create_engine(url, pool_pre_ping=True)
# Session = sessionmaker(bind=engine)
# with Session() as s:
#     n = s.execute(text("select count(*) from usergroup")).scalar_one()
#     print(n)
