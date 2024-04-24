# TODO - move to ovos-plugin-manager

import abc
from typing import List, Optional, Dict, Tuple

import numpy as np


class EmbeddingsDB:
    """base plugin for embeddings database"""

    @abc.abstractmethod
    def add_embeddings(self, key: str,
                       embedding: np.ndarray) -> np.ndarray:
        """store 'embeddings' under 'key' with associated 'metadata'"""
        return NotImplemented

    @abc.abstractmethod
    def get_embedding(self, key: str) -> np.ndarray:
        return NotImplemented

    @abc.abstractmethod
    def delete_embeddings(self, key: str) -> np.ndarray:
        """delete embeddings stored under 'key'"""
        return NotImplemented

    @abc.abstractmethod
    def query(self, embeddings: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """return top_k embeddings searching for closest entries to 'embeddings'"""
        return NotImplemented

    def distance(self, embeddings_a: np.ndarray,
                 embeddings_b: np.ndarray,
                 metric: str = "cosine") -> float:
        if metric == "cosine":
            dot = np.dot(embeddings_a, embeddings_b)
            norma = np.linalg.norm(embeddings_a)
            normb = np.linalg.norm(embeddings_b)
            cos = dot / (norma * normb)
            return 1 - cos
        else:
            raise ValueError("Unsupported metric")


class FaceRecognizer:
    def __init__(self, db: EmbeddingsDB, thresh: float = 0.15):
        self.db = db
        self.thresh = thresh

    @abc.abstractmethod
    def get_face_embeddings(self, frame: np.ndarray) -> np.ndarray:
        """a opencv image from a OVOS camera, assumed to contain 1 single face"""
        return NotImplemented

    def add_face(self, user_id: str,
                 frame: np.ndarray):
        emb: np.ndarray = self.get_face_embeddings(frame)
        return self.db.add_embeddings(user_id, emb)

    def delete_face(self, user_id: str):
        return self.db.delete_embeddings(user_id)

    def predict(self, frame: np.ndarray, top_k: int = 3) -> Optional[str]:
        """return top face searching for closest entries to 'frame'"""
        matches = self.query(frame, top_k)
        best = min(matches, key=lambda k: k[1])
        if best[1] > self.thresh:
            return None
        return best[0]

    def query(self, frame: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """return top_k embeddings searching for closest entries to 'embeddings'"""
        emb: np.ndarray = self.get_face_embeddings(frame)
        return self.db.query(emb, top_k)

    def distance(self, face_a: np.ndarray, face_b: np.ndarray,
                 metric: str = "cosine") -> float:
        """calc distance between 2 face embeddings"""
        emb: np.ndarray = self.get_face_embeddings(face_a)
        emb2: np.ndarray = self.get_face_embeddings(face_b)
        return self.db.distance(emb, emb2, metric)


class VoiceRecognizer:
    def __init__(self, db: EmbeddingsDB, thresh: float = 0.75):
        self.db = db
        self.thresh = thresh

    @staticmethod
    def audiochunk2array(audio_data: bytes):
        # Convert buffer to float32 using NumPy
        audio_as_np_int16 = np.frombuffer(audio_data, dtype=np.int16)
        audio_as_np_float32 = audio_as_np_int16.astype(np.float32)

        # Normalise float32 array so that values are between -1.0 and +1.0
        max_int16 = 2 ** 15
        data = audio_as_np_float32 / max_int16
        return data

    @abc.abstractmethod
    def get_voice_embeddings(self, audio_data: np.ndarray) -> np.ndarray:
        """audio data from a OVOS microphone"""
        return NotImplemented

    def add_voice(self, user_id: str,
                  audio_data: np.ndarray):
        emb: np.ndarray = self.get_voice_embeddings(audio_data)
        return self.db.add_embeddings(user_id, emb)

    def delete_voice(self, user_id: str):
        return self.db.delete_embeddings(user_id)

    def predict(self, frame: np.ndarray, top_k: int = 3) -> Optional[str]:
        """return top face searching for closest entries to 'frame'"""
        matches = self.query(frame, top_k)
        best = min(matches, key=lambda k: k[1])
        if best[1] > self.thresh:
            return None
        return best[0]

    def query(self, frame: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """return top_k embeddings searching for closest entries to 'embeddings'"""
        emb: np.ndarray = self.get_voice_embeddings(frame)
        return self.db.query(emb, top_k)

    def distance(self, voice_a: np.ndarray, voice_b: np.ndarray,
                 metric: str = "cosine") -> float:
        """calc distance between 2 voice embeddings"""
        emb: np.ndarray = self.get_voice_embeddings(voice_a)
        emb2: np.ndarray = self.get_voice_embeddings(voice_b)
        return self.db.distance(emb, emb2, metric)

