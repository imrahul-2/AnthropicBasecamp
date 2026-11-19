# PITCH.md

Six lines and a lever. Your words. The last two are scored.

Built: A customer-care agent for disrupted flights. It uses Larkspur's nine tools plus two of ours: seats_left, which we wrote, and fare_rules, which it reaches over MCP.
Does: It finds the passenger's booking, searches for alternative flights with seats free, holds one, and explains the fare rules in plain words.
Number: Input tokens across the five test tickets went from 61,706 to 64,120 per run.
Safety check: The agent holds a seat but never books it. Only the customer's own click confirms a booking. We saw this in the trace for K7PQ2M.
Next: Answer customers in Spanish as well as English.
Still broken: If a customer sends two booking codes in one message, the agent looks up only the first.
Lever: intelligence

## Priya asked

Costs:
Wrong:
Runs it:
Left out:
