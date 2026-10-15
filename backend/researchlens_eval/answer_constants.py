"""Fixed answer-study limits; changing these requires a new approved plan."""

from researchlens.defaults import ANSWER_OUTPUT_TOKENS, DEFAULT_CONTEXT_CHARS

from researchlens_eval.answer_judge_v2 import OUTPUT_TOKENS

JUDGE_OUTPUT = OUTPUT_TOKENS
GENERATION_OUTPUT = ANSWER_OUTPUT_TOKENS
CONTEXT_CHARS = DEFAULT_CONTEXT_CHARS
STUDY_CASES = 50
TOKEN_FRAMING_ALLOWANCE = 8192
