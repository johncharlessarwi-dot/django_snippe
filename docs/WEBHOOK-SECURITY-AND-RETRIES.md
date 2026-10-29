# Webhook verification and retry guidance

This guide describes secure integration expectations for webhook consumers using Django Snippe.

## Verification
- Verify provider signatures using the provider's documented algorithm and the raw request body.
- Keep signing secrets in environment-backed secret storage; never commit them.
- Compare signatures in constant time when the language/runtime supports it.
- Reject malformed timestamps and apply a bounded replay window when the provider supports signed timestamps.
- Do not trust event fields until signature verification succeeds.

## Idempotency
- Store provider event identifiers with a uniqueness constraint.
- Make handlers safe to receive the same event more than once.
- Use database transactions for state changes and event processing records.
- Return provider-appropriate success responses only after durable acceptance.

## Reliability
- Bound retries and use backoff for transient failures.
- Send permanently invalid events to a reviewable dead-letter path.
- Avoid retrying non-idempotent external side effects without a deduplication strategy.
- Redact secrets and personal data from logs.

## Testing
Cover valid signatures, invalid signatures, duplicate events, stale timestamps, malformed payloads, provider timeouts, and database rollback.