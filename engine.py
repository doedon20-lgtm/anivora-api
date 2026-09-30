import torch
from transformers import pipeline
from engine_config import EngineConfig


class AniVoraEngine:

    def __init__(self):
        self.name = "AniVora Engine"
        self.version = "0.3.1"
        self.model_name = EngineConfig.MODEL_NAME
        self.pipeline = None
        self.loaded = False
        self.device = self._detect_device()

    def _detect_device(self):

        if EngineConfig.DEVICE == "cpu":
            return "cpu"

        if EngineConfig.DEVICE == "cuda":

            if not torch.cuda.is_available():
                print("CUDA requested but no GPU is available.")
                print("Falling back to CPU.")
                return "cpu"

            return "cuda"

        if torch.cuda.is_available():
            return "cuda"

        return "cpu"

    def load(self):

        if self.loaded:
            return

        print("Loading AniVora Engine...")
        print(f"Model: {self.model_name}")
        print(f"Device: {self.device}")

        device = 0 if self.device == "cuda" else -1

        self.pipeline = pipeline(
            "text-generation",
            model=self.model_name,
            device=device
        )

        self.loaded = True

        print("AniVora Engine loaded successfully.")

    def generate(
        self,
        prompt,
        max_new_tokens=None,
        temperature=None
    ):

        if not prompt or not prompt.strip():
            raise ValueError(
                "Prompt cannot be empty"
            )

        self.load()

        if max_new_tokens is None:
            max_new_tokens = EngineConfig.MAX_NEW_TOKENS

        if temperature is None:
            temperature = EngineConfig.TEMPERATURE

        result = self.pipeline(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=True,
            return_full_text=False
        )

        if not result:
            raise RuntimeError(
                "AniVora model returned no output."
            )

        return result[0].get(
            "generated_text",
            ""
        ).strip()


_engine = None


def get_engine():

    global _engine

    if _engine is None:
        _engine = AniVoraEngine()

    return _engine
