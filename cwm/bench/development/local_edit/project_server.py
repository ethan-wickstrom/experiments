"""Serve localized edits and independent consequence queries using one loaded checkpoint."""
import argparse
import json
import sys

from backbone import chat_ids
from edit import Editor
from inference import generate


def respond(editor, request):
    if not isinstance(request, dict):
        raise ValueError("Expected a project model request")
    if set(request) == {"edit"}:
        return editor(request["edit"])
    if set(request) != {"forecast"} or not isinstance(request["forecast"], str):
        raise ValueError("Expected an edit or forecast")
    prompt = request["forecast"]
    count = len(chat_ids(editor.tok, prompt))
    if count > editor.max_input or count + 8 > editor.model.config.max_position_embeddings:
        raise ValueError("Forecast exceeds model context budget")
    answer, = generate(editor.model, editor.tok, [prompt], 8)
    return dict(text=answer["text"], finish="stop" if answer["stopped"] else "length",
                inputTokens=count, tokens=answer["tokens"] + int(answer["stopped"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", required=True, action="store_true")
    parser.add_argument("--arm", choices=["trained", "edit-only", "base"], default="trained")
    editor = Editor(parser.parse_args().arm)
    for line in sys.stdin:
        try:
            result = respond(editor, json.loads(line))
        except (ValueError, TypeError) as error:
            result = dict(stopped=False, error=str(error))
        print(json.dumps(result, allow_nan=False), flush=True)
