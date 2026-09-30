import os


class AniVoraEngine:
    """
    AniVora's model runtime.

    The API talks to this engine.
    The engine talks to the actual neural-network model.

    This separation lets us later move from CPU
    to GPU workers without rebuilding the API.
    """

    def __init__(self):

        self.name = "AniVora Engine"
        self.version = "0.2.0"

        self.model_name = os.getenv(
            "ANIVORA_MODEL",
            "Qwen/Qwen3-0.6B"
        )

        self.pipeline = None
        self.loaded = False

    def load(self):

        if self.loaded:
            return

        try:

            from transformers import pipeline

            self.pipeline = pipeline(
                "text-generation",
                model=self.model_name
            )

            self.loaded = True

        except Exception as error:

            raise RuntimeError(
                "AniVora model could not be loaded: "
                + str(error)
            )

    def generate(
        self,
        prompt,
        max_new_tokens=128,
        temperature=0.7
    ):

        if not prompt or not prompt.strip():

            raise ValueError(
                "Prompt cannot be empty"
            )

        self.load()

        result = self.pipeline(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=True,
            return_full_text=False
        )

        if not result:

            raise RuntimeError(
                "AniVora model returned no output"
            )

        generated = result[0].get(
            "generated_text",
            ""
        )

        return generated.strip()


_engine = None


def get_engine():

    global _engine

    if _engine is None:

        _engine = AniVoraEngine()

    return _engine
