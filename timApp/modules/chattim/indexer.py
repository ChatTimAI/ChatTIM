from http.client import responses

from google import genai
from dataclasses import dataclass, asdict
from typing import Protocol
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import json


@dataclass
class TextChunks:
    """text chunks to vectorize"""

    chunks: list[str]


@dataclass
class EmbeddingResponse:
    """list containing embeddings returned from the model"""

    embeddings: list[list[float]]


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


# TODO tiedoston haku tietokannasta


class TextChunkerHTML:
    def __init__(self, text: str):
        self.text = text

    def split_sentence(self) -> TextChunks:
        soup = BeautifulSoup(self.text, "html.parser")
        self.text = soup.get_text(strip=True)
        chunks = TextChunks(chunks=self.text.split(". "))
        return chunks

    def split_paragraph(self) -> TextChunks:
        soup = BeautifulSoup(self.text, "html.parser")
        paragraphs = soup.find_all("p")

        paragraphs_text = []
        for p in paragraphs:
            text = p.get_text()
            paragraphs_text.append(text)
        # vain ensimmäiset 20 kappaletta ilmaisen avaimen takia
        paragraphs = TextChunks(chunks=paragraphs_text[0:20])
        return paragraphs


# TODO mallin valinta,
#  mahdollisesti mallikohtaisia asetuksia?(task type,vektorin koko jne)
class EmbeddingModel(Protocol):
    def generate(self, text_chunks: TextChunks) -> EmbeddingResponse:
        ...


# TODO virheiden käsittely,
class GeminiEmbeddingModel(EmbeddingModel):
    """gemini implementation of embedding model"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, chunks: TextChunks) -> EmbeddingResponse:
        """generates embeddings from provided chunks"""

        text = chunks.chunks
        client = genai.Client(api_key=self.api_key)

        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
        )
        embeddings = [x.values for x in result.embeddings]

        return EmbeddingResponse(embeddings=embeddings)

    def create_embeddings(self):
        """generates the data object containing embeddings and corresponding text chunks"""

        with open("llm_wiki.htm", "r") as file:
            page = file.read()

        chunks = TextChunkerHTML(page).split_paragraph()

        embeddings = self.generate(chunks)

        ids = list(range(len(chunks.chunks)))
        data = [
            EmbeddingData(embedding=embedding, text=text, id=i)
            for (embedding, text, i) in zip(embeddings.embeddings, chunks.chunks, ids)
        ]
        with open("embeddings.json", "w") as f:
            json.dump(data, f, indent=2)
        return data


def get_embeddings(doc_id: int) -> list[EmbeddingData]:
    response: list[EmbeddingData] = [None]
    return response


# TODO tietokantaan tallennus, promptia vastaavien tekstipätkien hakeminen
def getContext(doc_id: int, prompt: str, k: int = 5):
    # needs fix...
    prompt = TextChunks(chunks=[prompt])
    prompt_embedding = GeminiEmbeddingModel(api_key="").generate(prompt)
    page_embeddings: list[EmbeddingData] = get_embeddings(doc_id)
    similarities: list[list[str, float]] = []
    for chunk in page_embeddings:
        similarity = cosine_similarity(chunk.embedding, prompt_embedding)
        similarities.append([chunk.text, similarity])

    similarities.sort(key=lambda x: x[0], reverse=True)
    best_chunks = similarities[0:k]
    return best_chunks


def test():
    return GeminiEmbeddingModel(api_key="").create_embeddings()
