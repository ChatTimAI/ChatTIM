from google import genai
from dataclasses import dataclass, asdict
from typing import Protocol
from bs4 import BeautifulSoup
import json
from openai import OpenAI
import numpy as np

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
        # needs better sentence splitting
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


class TextChunker:
    def __init__(self, text: str):
        self.text = text

    def split_sentence(self) -> TextChunks:
        # needs better sentence splitting
        return TextChunks(chunks=self.text.split(". "))

    # splits every 600 characters, includes 100 from last chunk
    def split(self, chunk_size: int = 600, overlap: int = 100):
        chunks = []
        start = 0
        while start < len(self.text):
            end = start + chunk_size
            chunks.append(self.text[start:end])
            start += chunk_size - overlap
        return TextChunks(chunks=chunks)

    def split2(self, max_chunk_size: int = 600, overlap: int = 100):
        chunks = []
        sentences = self.text.split(". ")
        current_chunk = ""
        for sentence in sentences:
            if (len(current_chunk) + len(sentence)) < max_chunk_size:
                current_chunk += sentence + ". "
            else:
                chunks.append(current_chunk)
                overlapping_text = current_chunk[overlap:]
                current_chunk += overlapping_text + ". " + sentence
        if (len(current_chunk)) > 0:
            chunks.append(current_chunk)


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
        self.client = genai.Client(api_key=self.api_key)

    def generate(self, chunks: TextChunks) -> EmbeddingResponse:
        """generates embeddings from provided chunks"""

        text = chunks.chunks

        try:
            result = self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
            )
        except Exception as e:
            return f"Error generating embeddings {e}"
        embeddings = [x.values for x in result.embeddings]

        return EmbeddingResponse(embeddings=embeddings)


class OpenAiEmbeddingModel(EmbeddingModel):
    """openai implementation of embedding model"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)

    def generate(self, chunks: TextChunks):
        """generates embeddings from provided chunks"""
        text = chunks.chunks

        try:
            result = self.client.embeddings.create(
                input=text, model="text-embedding-3-small"
            )
        except Exception as r:
            print("Error generating embeddings", r)
            return EmbeddingResponse(embeddings=[])

        embeddings = [x.embedding for x in result.data]
        return EmbeddingResponse(embeddings=embeddings)


def create_embeddings():
    """generates the data object containing embeddings and corresponding text chunks"""

    with open("llm_wiki.htm", "r") as file:
        page = file.read()

    chunks = TextChunkerHTML(page).split_paragraph()

    embeddings = GeminiEmbeddingModel(api_key="").generate(chunks)
    # embeddings = self.generate(chunks)
    ids = list(range(len(chunks.chunks)))
    data = [
        EmbeddingData(embedding=embedding, text=text, id=i)
        for (embedding, text, i) in zip(embeddings.embeddings, chunks.chunks, ids)
    ]
    data_dict = [asdict(obj) for obj in data]
    try:
        with open("/tmp/embeddings.json", "w") as f:
            json.dump(data_dict, f, indent=2)
    except Exception as e:
        return f"Error saving embeddings {e}"
    return data


def get_embeddings():
    try:
        with open("/tmp/embeddings.json", "r") as file:
            page_embeddings = json.load(file)
    except Exception as e:
        return f"Error retrieving embeddings {e}"
    return page_embeddings


def get_context(prompt: str, k: int = 5, doc_id: int = None):
    prompt = TextChunks(chunks=[prompt])
    try:
        prompt_embedding = GeminiEmbeddingModel(api_key="").generate(prompt)
        prompt_embedding = np.array(prompt_embedding.embeddings[0])
    except Exception as e:

        return f'Prompt embedding error: {e}'
    page_embeddings = get_embeddings()

    embeddings = []
    texts = []
    for chunk in page_embeddings:
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
    return best_chunks
