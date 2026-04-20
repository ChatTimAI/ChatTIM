from dataclasses import dataclass, asdict
from typing import Protocol
import json
from openai import OpenAI
import numpy as np

from timApp.document.document import Document
from timApp.modules.chattim.database_handler import TimDatabase


# TODO mallien määrittely/valinta Indexer luokkaan?
@dataclass
class TextChunks:
    """text chunks to vectorize"""

    chunks: list[str]


@dataclass
class EmbeddingResponse:
    """list containing embeddings returned from the model"""

    embeddings: list[list[float]]
    used_tokens: int


@dataclass
class ContextResponse:
    """list containing context returned from the model"""

    context: str
    tokens_used: int


@dataclass
class EmbeddingData:
    """embedding and
    corresponding text chunk.
    file/tim page name or address?
    chunk id
    """

    embedding: list[float]
    text: str
    id: int
    # filename: str


# TODO mallin valinta,
#  mahdollisesti mallikohtaisia asetuksia?(task type,vektorin koko jne)
class EmbeddingModel(Protocol):
    def generate(self, text_chunks: TextChunks) -> EmbeddingResponse:
        ...


class GeminiEmbeddingModel(EmbeddingModel):
    """gemini implementation of embedding model"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None

    def generate(self, chunks: TextChunks) -> EmbeddingResponse:
        """generates embeddings from provided chunks"""
        if self.client is None:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            )
            # self.client = genai.Client(api_key=self.api_key)

        text = chunks.chunks

        try:
            result = self.client.embeddings.create(
                input=text, model="gemini-embedding-001"
            )
            # result = self.client.models.embed_content(model="gemini-embedding-001",contents=text,)
        except Exception as e:
            print(f"Error generating embeddings {e}")
            return EmbeddingResponse(embeddings=[], used_tokens=0)

        embeddings = [x.embedding for x in result.data]

        return EmbeddingResponse(
            embeddings=embeddings, used_tokens=result.usage.total_tokens
        )


class OpenAiEmbeddingModel(EmbeddingModel):
    """openai implementation of embedding model"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)

    def generate(self, chunks: TextChunks) -> EmbeddingResponse:
        """generates embeddings from provided chunks"""

        text = chunks.chunks

        try:
            result = self.client.embeddings.create(
                input=text, model="text-embedding-3-small"
            )

        except Exception as r:
            print("Error generating embeddings", r)
            return EmbeddingResponse(embeddings=[], used_tokens=0)

        embeddings = [x.embedding for x in result.data]

        return EmbeddingResponse(
            embeddings=embeddings, used_tokens=result.usage.total_tokens
        )


# TODO tekstin paloitteluun eri vaihtoehtoja
class Indexer:
    def __init__(self, embedding_model: EmbeddingModel, indexed_page_ids):
        self.embedding_model = embedding_model
        self.indexed_page_ids = indexed_page_ids
        # self.text_chunker = text_chunker

    def delete_page(self, doc_id) -> bool:
        """Deletes the page from the index. Returns True if the page was deleted"""
        if doc_id in self.indexed_page_ids:
            self.indexed_page_ids.remove(doc_id)
            return True
        else:
            return False

    # tätä ei ehkä tarvita enään
    def chunk_text(self, text, max_chunk_size: int = 600, overlap: int = 100):
        chunks = []
        sentences = text.split(". ")
        current_chunk = ""

        for sentence in sentences:
            if (len(current_chunk) + len(sentence)) < max_chunk_size:
                current_chunk += sentence + ". "
            else:
                chunks.append(current_chunk)
                overlapping_text = current_chunk[-overlap:]
                current_chunk = overlapping_text + ". " + sentence
        if (len(current_chunk)) > 0:
            chunks.append(current_chunk)
        return TextChunks(chunks=chunks)

    # TODO ei haeta mahdollisia plugin lohkoja
    def get_tim_blocks(self, doc: Document) -> TextChunks:
        try:
            blocks = doc.export_raw_data()
            text = [block["md"] for block in blocks]
        except Exception as e:
            print(f"Error getting tim blocks {e}")

        return TextChunks(chunks=text)

    def create_embeddings(self, documents: list[Document]) -> int:
        """generates the data object containing embeddings and corresponding text chunks,returns the number of tokens used"""
        tokens_used = 0
        for document in documents:
            chunks = self.get_tim_blocks(doc=document)

            embeddings = self.embedding_model.generate(chunks)
            tokens_used += embeddings.used_tokens
            ids = list(range(len(chunks.chunks)))

            data = [
                EmbeddingData(embedding=embedding, text=text, id=i)
                for (embedding, text, i) in zip(
                    embeddings.embeddings, chunks.chunks, ids
                )
            ]
            data_dict = [asdict(obj) for obj in data]
            file_name = document.doc_id
            try:
                with open(f"modules/chattim/{file_name}.json", "w") as f:
                    json.dump(data_dict, f, indent=2)
            except Exception as e:
                print(f"Error saving embeddings {e}")

        return tokens_used

    def get_embeddings(
        self,
    ):
        page_embeddings = []
        print(f"indexed_page_ids{self.indexed_page_ids}")
        for doc_id in self.indexed_page_ids:
            try:
                with open(f"modules/chattim/{doc_id}.json", "r") as file:
                    page_embeddings.append(json.load(file))
            except Exception as e:
                print(f"Error retrieving embeddings {e}")

        return page_embeddings

    def get_context(self, prompt: str, k: int = 3) -> ContextResponse:
        """returns the context for the prompt as list of text,and the number of tokens used,"""
        prompt = TextChunks(chunks=[prompt])
        tokens_used = 0
        try:
            prompt_embedding = self.embedding_model.generate(prompt)
            tokens_used = prompt_embedding.used_tokens
            prompt_embedding = np.array(prompt_embedding.embeddings[0])

        except Exception as e:
            return f"Prompt embedding error: {e}"
        page_embeddings = self.get_embeddings()

        embeddings: list[float] = []
        texts = []
        print(f"page embeddings{page_embeddings}")
        for page in page_embeddings:
            for chunk in page:
                print(chunk["embedding"])
                embeddings.append(chunk["embedding"])
                texts.append(chunk["text"])

        embeddings = np.array(embeddings)

        # manual cosine similarity
        dot_product = embeddings @ prompt_embedding
        norm_embeddings = np.linalg.norm(embeddings, axis=1)
        norm_prompt = np.linalg.norm(prompt_embedding)
        similarities = dot_product / (norm_embeddings * norm_prompt)

        data = [[t, e] for t, e in zip(texts, similarities)]

        data.sort(key=lambda x: x[1], reverse=True)

        best_chunks = data[0:k]
        context = []

        [context.append(text) for text, similarity in best_chunks]
        context = ", ".join(context)
        return ContextResponse(context=context, tokens_used=tokens_used)
