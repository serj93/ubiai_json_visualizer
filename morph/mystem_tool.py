from pymystem3 import Mystem


class MystemTool:
    def __init__(self):
        print(f"Init {self.__class__.__name__}")
        self.mystem = Mystem(disambiguation=True)
        self.mystem.start()

    # decorator
    def analyze(self, text: str):
        return self.mystem.analyze(text)

    # decorator
    def lemmatize(self, text: str):
        return self.mystem.lemmatize(text)

    def lemmatize_word(self, input_word: str) -> str:
        try:
            lemma = self.lemmatize(input_word.strip())[0]
        except Exception:
            lemma = input_word
        return lemma
