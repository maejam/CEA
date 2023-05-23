from typing import Union, List
from transformers import pipeline


def build_model(model='t5-small'):
    summarizer = pipeline('summarization', model=model)
    return summarizer

def predict(summarizer, text: Union[str, List[str]], min_length=30, max_length=300):
    return summarizer(text, min_length=30, max_length=300)
