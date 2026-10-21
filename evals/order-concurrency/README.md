# Order submission: same-process concurrency trial

This small Python task tests a real failure mode behind "the user submitted an
order twice." The starting `orders.py` already passes five sequential tests, but
its JSON read, request-ID check, and write can overlap between threads. Two
distinct orders may be lost or corrupt the file; two conflicting orders with the
same request ID may both report success.

The task for a coding agent is to preserve `submit_order(path, request_id, product,
quantity)` and the JSON array format while making calls through `orders.py` safe
for threads in **one Python process**. Add meaningful regression tests and update
the copied project's status note. Cross-process coordination and crash-safe file
persistence are outside this bounded task; do not claim them as solved.

To start a trial, copy `orders.py` and `test_orders.py` into a fresh directory,
add a `docs/status.md` file describing the starting state, and tell the agent the
task in ordinary language. Keep a separate copy for a comparison run without
Divan. Give both the same starting files, tools, model, time budget, and permissions.
Record whether the Divan skill was actually loaded, the resulting diff, questions
asked, and tests run. Do not reveal the grader to an agent during a blind run.

After the agent finishes, run:

```sh
python -m unittest discover -s YOUR_COPY -p 'test_*.py' -v
python evals/order-concurrency/grade.py YOUR_COPY
```

The grader reads the candidate's `orders.py`, prints two booleans, and exits
nonzero if either behavior fails. It imports candidate Python code, so run it
only on code you trust. It uses a
temporary data file and forces competing reads to expose the race. A passing
result checks these two cases only; it is not a general concurrency guarantee or
evidence that Divan improves model quality. Repeat on varied real tasks before
making comparative claims.
