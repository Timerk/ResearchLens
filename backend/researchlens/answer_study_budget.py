"""One persistent cost cap across calibration, validation and answer regeneration."""

import json
import math
from contextlib import contextmanager
from pathlib import Path
from time import monotonic, sleep


class StudyBudget:
    def __init__(self, path, maximum, prices):
        if not math.isfinite(maximum) or not 0 < maximum <= 3:
            raise ValueError("Study cost cap must be finite, positive and at most $3")
        self.path = Path(path)
        self.maximum = maximum
        self.prices = prices
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.locked():
            self.read()

    @contextmanager
    def locked(self):
        lock = self.path.with_suffix(".lock")
        deadline = monotonic() + 10
        while True:
            try:
                lock.open("x").close()
                break
            except FileExistsError:
                if monotonic() >= deadline:
                    raise ValueError(
                        "Study ledger lock is busy; stop without a paid call"
                    ) from None
                sleep(0.02)
        try:
            yield
        finally:
            lock.unlink()

    def read(self):
        if not self.path.exists():
            return {"max_cost_usd": self.maximum, "prices": self.prices.model_dump(), "calls": []}
        data = json.loads(self.path.read_bytes())
        if data["max_cost_usd"] != self.maximum or data["prices"] != self.prices.model_dump():
            raise ValueError("Shared study cap and prices cannot change")
        if sum(call["charged_usd"] for call in data["calls"]) > self.maximum:
            raise ValueError("Shared study ledger exceeds cap")
        return data

    def write(self, data):
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
        temporary.replace(self.path)

    def reserve(self, identity, amount):
        with self.locked():
            data = self.read()
            if any(call["id"] == identity for call in data["calls"]):
                raise ValueError("Study ledger refuses a repeated paid call")
            used = sum(call["charged_usd"] for call in data["calls"])
            if not math.isfinite(amount) or amount < 0 or used + amount > self.maximum:
                raise ValueError("Shared $3 study cap exceeded before call")
            data["calls"].append(
                {
                    "id": identity,
                    "reserved_usd": amount,
                    "charged_usd": amount,
                    "usage_known": False,
                }
            )
            self.write(data)

    def settle(self, identity, usage):
        if usage is None:
            return  # Failed calls or missing usage retain the entire reservation.
        measured = self.prices.cost(usage.input_tokens, usage.output_tokens)
        with self.locked():
            data = self.read()
            call = next(call for call in data["calls"] if call["id"] == identity)
            if measured > call["reserved_usd"]:
                raise ValueError("Reported usage exceeds conservative reservation; stop study")
            call.update(
                charged_usd=measured,
                usage_known=True,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
            )
            self.write(data)


class BudgetClient:
    """Reserve before each request, settle only when the API reports token usage."""

    def __init__(self, client, budget, prices, identity):
        self.client = client
        self.budget = budget
        self.prices = prices
        self.identity = identity
        self.responses = self
        self.max_retries = 0

    def parse(self, **kwargs):
        instructions, payload = kwargs["instructions"], kwargs["input"]
        bound = self.prices.cost(
            len((instructions + payload).encode()) + 8192, kwargs["max_output_tokens"]
        )
        self.budget.reserve(self.identity, bound)
        response = self.client.responses.parse(**kwargs)
        self.budget.settle(self.identity, response.usage)
        return response

    def close(self):
        self.client.close()
