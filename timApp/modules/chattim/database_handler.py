from dataclasses import dataclass
from timApp.document import docentry
from timApp.item.item import Item
from timApp.user.user import User
from timApp.auth.get_user_rights_for_item import (
    get_user_rights_for_item,
    UserItemRights,
)


@dataclass
class TimDatabase:
    @staticmethod
    def identify_user(user_id: int):
        """
        Cheks if the given user is a teacher or a student
        """
        teacher = User.get_by_id(user_id).is_sisu_teacher
        if teacher:
            return "teacher"
        student = User.get_home_org_student_id(User.get_by_id(user_id))
        if student:
            return "student"
        return "user"  # TODO: better options

    @staticmethod
    def get_tim_pages_by_id(id_list: list[int]):
        """
        Returns a list of pages corresponding to the given list of ids.
        """
        doc_entries = docentry.get_documents(custom_filter=id(id_list))
        documents = []
        for d in doc_entries:
            documents.append(d.document)
        return documents

    @staticmethod
    def get_tim_pages_by_path(path: str):
        """
        Returns a list of pages corresponding to the given path.
        """
        doc_entries = docentry.get_documents(filter_folder=path)
        documents = []
        for d in doc_entries:
            documents.append(d.document)
        return documents

    @staticmethod
    def check_rights(user_id: int, doc_id: int) -> UserItemRights:
        """
        Checks if the given user has the rights to the given document.
        """
        user = User.get_by_id(user_id)
        doc = Item.find_by_id(doc_id)
        rights = get_user_rights_for_item(doc, user)
        return rights
