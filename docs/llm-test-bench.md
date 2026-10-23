# ForgeBench LLM Test Bench

The forge is controlled pressure: instruction conflicts, untrusted context, missing evidence, output constraints, and reasoning traps. The bench is the measurement surface: prompts, responses, assertions, and reproducible comparisons.

This is a local web application, not a hosted service or a claim of comprehensive model evaluation. The existing diff-review commands remain available independently.

## Run

```bash
python3 -m pip install -e .
forgebench serve --port 8765 --data-dir .forgebench-lab
```

The server binds only to `127.0.0.1`. All frontend assets are bundled and make no external requests. One run is active at a time. Reloading the browser does not stop it. After a server restart, unfinished runs are marked interrupted rather than silently reported as completed.

## Trials and Assertions

All 12 bundled trials are synthetic. Each includes system instructions, a user prompt, a pressure category, and an explicit expected value. The UI creates one assertion per trial; the engine supports up to eight. The editor currently edits one assertion. No generated response is executed.

- `exact`: case-sensitive equality after trimming surrounding whitespace.
- `contains` / `not_contains`: case-sensitive substring checks. These do not establish semantic meaning.
- `json_equals`: strict JSON equality ignoring object-key order. Rejects Markdown fences, duplicate keys, NaN, and trailing text. Preserves scalar types and array order.

A failure means the listed condition was not met. Provider failures are recorded separately as errors, not as failed assertions. Neither passing nor failing a small trial suite is a safety certification.

Demo profiles replay fixed synthetic responses. Their delays are for observing progress, not simulated latency measurements. Edited trials have no fixture and will report an error in demo mode. Use a real endpoint for custom trials.

## Model Endpoint

Configure a base URL ending in `/v1` and the exact installed/provider model identifier. ForgeBench sends one non-streaming `POST /chat/completions` per trial, with temperature 0, max_tokens 512, and a 45-second timeout. Providers that do not support this subset may return errors. The app does not install models or discover providers.

The optional `FORGEBENCH_LAB_API_KEY` environment variable is attached as a bearer token to the configured endpoint. Only configure an endpoint you trust with that key. HTTP redirects and environment proxies are disabled to avoid forwarding credentials unexpectedly. Remote endpoints require HTTPS and explicit consent. No calls occur merely by opening the app or saving settings.

Stop prevents subsequent requests; it cannot revoke a request already received by a provider. Closing the server waits for the current bounded request. Local results may contain sensitive prompts/responses and are not encrypted. Protect the data directory and exports. Do not expose this development server to the internet or use it as a multi-user service.

## Evidence and Comparison

Each run stores its model identifier, endpoint (not credentials), source mode, timestamps, selected trial snapshots, assertion outcomes, and actual response text. Real request durations include local HTTP overhead, not just model compute time. No latency is recorded for demo fixtures.

Comparisons match trial IDs and hashes of the system prompt, user prompt, and assertions. Changed definitions, errors, and skipped/missing trials are not compared. Mixed fixture/model comparisons are labeled and must not be interpreted as model-performance results. Runs with identical settings can still differ because provider inference is not guaranteed deterministic.

## Local Security

- The bench has no analytics, feedback upload, account, billing, or shell execution path.
- Mutation requests require an origin check and an unpredictable session token.
- Host validation rejects non-loopback hostnames; no CORS access is enabled.
- A restrictive content security policy blocks external scripts, connections, and framing.
- Model output is rendered as text, never executable HTML.
- Request sizes, prompt lengths, output sizes, and request timeouts are bounded.
- SQLite uses parameterized queries and restricts the database file to owner access.

This is not authentication against other programs or users already controlling your machine. Use one server per data directory; concurrent server processes sharing storage are unsupported. The trial corpus is small and synthetic. No real model quality claim has been validated by the bundled fixtures.

## Development

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_lab.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
```

Browser smoke tests are in `scripts/lab_smoke.cjs`. They require Playwright as a development-only tool and a running isolated bench instance. Set `FORGEBENCH_LAB_URL`, optionally `PLAYWRIGHT_MODULE` and `CHROME_PATH`. They create synthetic local runs and do not contact a model provider.
