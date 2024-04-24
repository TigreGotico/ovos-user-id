from typing import List, Tuple

import numpy as np

from ovos_user_id.templates import EmbeddingsDB, FaceRecognizer

# TODO - own plugin repos
import chromadb
import face_recognition


class ChromaEmbeddingsDB(EmbeddingsDB):
    def __init__(self, path: str):
        super().__init__()
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection("embeddings",
                                                               metadata={"hnsw:space": "cosine"}  # l2 is the default
                                                               )

    def add_embeddings(self, key: str, embedding: np.ndarray) -> None:
        if isinstance(embedding, np.ndarray):
            embeddings = embedding.tolist()
        self.collection.upsert(
            embeddings=[embedding.tolist()],
            ids=[key]
        )

    def delete_embedding(self, key: str) -> None:
        self.collection.delete(ids=[key])

    def get_embedding(self, key: str) -> np.ndarray:
        e = self.collection.get(ids=[key], include=["embeddings"])['embeddings'][0]
        return np.array(e)

    def query(self, embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
        res = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k
        )
        ids = [i for i in res["ids"][0]]
        distances = [i for i in res["distances"][0]]
        return list(zip(ids, distances))


class FaceRecognitionPlugin(FaceRecognizer):
    def __init__(self, thresh: float = 0.75):
        path = "/tmp/face_db"  # TODO
        db = ChromaEmbeddingsDB(path)
        super().__init__(db, thresh)

    def get_face_embeddings(self, frame: np.ndarray) -> np.ndarray:
        return face_recognition.face_encodings(frame)[0]


if __name__ == "__main__":
    # Example usage:
    a = "/home/miro/PycharmProjects/ovos-user-id/a1.jpg"
    a2 = "/home/miro/PycharmProjects/ovos-user-id/a2.jpg"
    b = "/home/miro/PycharmProjects/ovos-user-id/b.jpg"

    f = FaceRecognitionPlugin()

    e1 = face_recognition.load_image_file(a)
    e2 = face_recognition.load_image_file(a2)
    b = face_recognition.load_image_file(b)

    f.add_face("arnold", e1)
    f.add_face("silvester", b)
    print(f.query(e1))
    print(f.query(e2))
    print(f.query(b))