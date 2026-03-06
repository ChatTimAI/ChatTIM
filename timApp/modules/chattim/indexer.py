from google import genai
from dataclasses import dataclass
from typing import Protocol


@dataclass
class TextChunks:
    """text chunks to vectorize"""

    chunks: list[str]


@dataclass
class Embedding:
    """single embedding vector"""

    embedding_vector: list[float]


@dataclass
class EmbeddingResponse:
    """list containing embeddings returned from the model"""

    embeddings: list[Embedding]


# lopullinen tallennettava objekti hakua varten,
# tälle ehkä kuvaavampi nimi(?) ja mahdollisesti muita kenttiä
@dataclass
class EmbeddingData:
    """embeddings
    corresponding text chunks.
    file/tim page name or address?
    chunk id
    """

    embeddings: list[Embedding]
    texts: TextChunks
    id: int
    filename: str


# TODO teksti paloittelu


# TODO mallin valinta,
#  mahdollisesti mallikohtaisia asetuksia?(task type,vektorin koko jne)
class EmbeddingModel(Protocol):
    def generate(self, text_chunks: TextChunks) -> EmbeddingResponse:
        ...


# TODO virheiden käsittely
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
        embeddings = [Embedding(embedding_vector=x.values) for x in result.embeddings]

        return EmbeddingResponse(embeddings=embeddings)


# TODO vektoroitu data muuntaa esim json muotoon ja tallentaa tietokantaan
