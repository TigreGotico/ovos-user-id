import abc
from typing import List, Optional, Dict, Tuple

import numpy as np


class EmbeddingsDB:
    """base plugin for embeddings database"""

    def __init__(self, path):
        self.path = path

    @abc.abstractmethod
    def add_embeddings(self, key: str,
                       embeddings: np.array,
                       metadata: Optional[Dict] = None) -> np.array:
        """store 'embeddings' under 'key' with associated 'metadata'"""
        return NotImplemented

    @abc.abstractmethod
    def delete_embeddings(self, key: str) -> np.array:
        """delete embeddings stored under 'key'"""
        return NotImplemented

    @abc.abstractmethod
    def query(self, embeddings: np.array, top_k: int = 5) -> List[Tuple[str, np.array]]:
        """return top_k embeddings searching for closest entries to 'embeddings'"""
        return NotImplemented

    @abc.abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, np.array]]:
        """return top_k embeddings searching the metadata for 'query'"""
        return NotImplemented

    @abc.abstractmethod
    def distance(self, embeddings_a: np.array, embeddings_b: np.array,
                 metric: str = "cosine") -> float:
        """calc distance between 2 embeddings"""
        return NotImplemented


class FaceRecognizer:
    def __init__(self, db: EmbeddingsDB, thresh: float = 0.75):
        self.db = db
        self.thresh = thresh

    @abc.abstractmethod
    def get_face_embeddings(self, frame: np.array) -> np.array:
        """a opencv image from a OVOS camera"""
        return NotImplemented

    def add_face(self, user_id: str,
                 frame: np.array,
                 metadata: Optional[Dict] = None):
        emb: np.array = self.get_face_embeddings(frame)
        return self.db.add_embeddings(user_id, emb, metadata)

    def delete_face(self, user_id: str):
        return self.db.delete_embeddings(user_id)

    def predict(self, frame: np.array, top_k: int = 5) -> Dict[str, float]:
        """return top_k faces searching for closest entries to 'frame'"""
        emb: np.array = self.get_face_embeddings(frame)
        matches: List[Tuple[str, np.array]] = self.db.query(emb, top_k)
        return {k: self.db.distance(emb, e) for k, e in matches}

    def distance(self, face_a: np.array, face_b: np.array,
                 metric: str = "cosine") -> float:
        """calc distance between 2 face embeddings"""
        emb: np.array = self.get_face_embeddings(face_a)
        emb2: np.array = self.get_face_embeddings(face_b)
        return self.db.distance(emb, emb2, metric)


class VoiceRecognizer:
    def __init__(self, db: EmbeddingsDB, thresh: float = 0.75):
        self.db = db
        self.thresh = thresh

    @abc.abstractmethod
    def get_voice_embeddings(self, audio_data: np.array) -> np.array:
        """audio data from a OVOS microphone"""
        return NotImplemented

    def add_voice(self, user_id: str,
                  audio_data: np.array,
                  metadata: Optional[Dict] = None):
        emb: np.array = self.get_voice_embeddings(audio_data)
        return self.db.add_embeddings(user_id, emb, metadata)

    def delete_voice(self, user_id: str):
        return self.db.delete_embeddings(user_id)

    def predict(self, audio_data: np.array, top_k: int = 5) -> Dict[str, float]:
        """return top_k voices searching for closest entries to 'audio_data'"""
        emb: np.array = self.get_voice_embeddings(audio_data)
        matches: List[Tuple[str, np.array]] = self.db.query(emb, top_k)
        return {k: self.db.distance(emb, e) for k, e in matches}

    def distance(self, voice_a: np.array, voice_b: np.array,
                 metric: str = "cosine") -> float:
        """calc distance between 2 voice embeddings"""
        emb: np.array = self.get_voice_embeddings(voice_a)
        emb2: np.array = self.get_voice_embeddings(voice_b)
        return self.db.distance(emb, emb2, metric)
