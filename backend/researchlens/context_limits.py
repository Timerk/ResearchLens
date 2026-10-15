import json

MAX_PASSAGES = 4
MAX_PASSAGE_CHARS = 3000
MAX_CONTEXT_CHARS = 16000

# Round a quote-escaped ASCII passage plus JSON overhead up to leave room for its ID.
MIN_CONTEXT_CHARS = (
    (len(json.dumps([{"id": "", "kind": "synthetic", "text": '"' * MAX_PASSAGE_CHARS}])) + 999)
    // 1000
    * 1000
)
