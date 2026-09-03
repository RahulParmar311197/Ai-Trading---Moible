# Portfolio Risk Monitoring

The portfolio-risk module is a deterministic monitoring primitive for the autonomous-trading foundation.

It computes:

- gross absolute notional exposure;
- signed net notional exposure;
- per-symbol position exposure;
- aggregate realized and unrealized P&L;
- pairwise Pearson correlation for positions with explicit aligned return histories.

Limits are evaluated fail-closed. Invalid/non-finite inputs, duplicate symbols, undefined correlation histories, and exceeded limits are rejected rather than approximated.

**Execution boundary:** this module does not place, cancel, modify, or authorize broker orders. An assessment is informational risk state and must remain subordinate to the existing deterministic execution/risk gate. No autonomous live-trading path is enabled by this module.
