# Reliability

- Retry only failures that may be transient.
- Use bounded retry with backoff when appropriate; do not retry validation failures.
- Give external calls explicit timeout/cancellation behavior where supported.
- Separate user-facing errors from internal diagnostic context.
- Use structured logs and correlation identifiers when the application already has observability.
- Never log secrets, authorization headers, private keys, or unnecessary personal data.
