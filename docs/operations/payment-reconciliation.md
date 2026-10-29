# Payment reconciliation procedure

Reconcile local payment records against the provider's authoritative transaction status. This procedure is for operational review and does not change payment processing code.

## Daily review

- Compare transaction references, amount, currency, and status for the review window.
- Identify payments pending beyond the provider's expected processing period.
- Flag duplicate references, amount mismatches, and unexpected terminal-state changes.
- Verify that successful payments have exactly one corresponding fulfillment record.

## Exception handling

1. Preserve the original transaction and webhook evidence.
2. Query the provider through the approved authenticated API.
3. Record the provider response reference and reconciliation decision.
4. Require a second reviewer for manual financial adjustments.
5. Never mark a payment successful solely because a browser redirect returned to the success page.

## Audit record

Capture the review period, operator, exception reference, provider status, action taken, reviewer, and completion time. Redact credentials and unnecessary customer information.