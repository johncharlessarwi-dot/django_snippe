# Payment state transition test matrix

Use this matrix when changing payment creation, status polling, webhook processing, or reconciliation. Exact provider statuses should be mapped to the states supported by the installed Snippe API version.

| Scenario | Expected behavior |
|---|---|
| Valid pending payment | Persist pending state; do not mark paid |
| Verified successful payment | Transition to paid once |
| Verified failed payment | Record failure without granting value |
| Duplicate success webhook | Idempotent no-op after first successful transition |
| Invalid webhook signature | Reject and do not mutate payment state |
| Stale or replayed event | Reject or safely ignore according to provider contract |
| Unknown payment reference | Do not create an unrelated payment |
| Provider timeout | Preserve last known state and allow safe retry |
| Conflicting terminal status | Reconcile against authoritative provider status and retain audit evidence |

## Assertions

- State transitions are monotonic unless an explicit reconciliation policy permits otherwise.
- Amount, currency, and merchant reference match the original payment intent.
- No callback alone grants access before authenticity and status are verified.
- Repeated requests do not duplicate fulfillment.
- Sensitive payment data is not written to logs.