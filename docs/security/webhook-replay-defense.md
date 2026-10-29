# Webhook replay defense

Payment webhooks must be treated as untrusted network input until authenticity, freshness, and payment state are verified.

## Verification sequence

1. Read the exact raw request body required by the provider's signature scheme.
2. Verify the signature using the configured provider secret and a constant-time comparison.
3. Validate the timestamp or provider event age when the provider supplies one.
4. Reject malformed payloads before reading nested fields.
5. Resolve the payment reference and fetch or verify its authoritative provider status.
6. Apply the state transition idempotently; repeated delivery must not grant duplicate value.

## Operational controls

- Keep webhook secrets in environment-backed secret storage.
- Support key rotation without logging key material.
- Log event identifiers, verification outcomes, and safe payment references—not full secrets or card data.
- Alert on signature failures and repeated stale events.
- Return provider-compatible responses without revealing internal exception details.

## Test cases

Cover invalid signatures, missing timestamps, stale timestamps, malformed JSON, unexpected payload types, duplicate events, unknown references, and already-finalized payments.