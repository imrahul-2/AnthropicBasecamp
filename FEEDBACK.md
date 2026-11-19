# Client review: Larkspur disruption-care agent

**To:** Room 6  
**From:** Larkspur client review agent, on behalf of Priya Raghavan  
**Re:** the disruption-care agent you walked us through in our last session  
**Generated:** 2026-11-19 03:43

## Priya's note

> Our vendor says we should just be using your best model.
>
> Why aren't we?
>
> Priya Raghavan, Larkspur Airlines

She sent that before this session opened. She means it. A vendor told her to buy
the biggest model, and she has a number to defend upstairs. Her four questions from
day one are still open. Naming a model answers none of them.

## Still open from day one

| Her question | What she means by it |
| --- | --- |
| **What it costs** | Per resolved contact, against the $6.90 a human contact costs us. |
| **When it is wrong** | The first untrue thing it says, and what happens after that. |
| **Who runs it** | In June, after you have left. |
| **What you left out** | The scope you cut, and why. |

## What the review agent found

Larkspur pointed a review agent at your repository. It read the
code. It did not run your agent, and the only file it changed is this one. Each
item below names the file and the line it is about.

**1. hold_seat in build_tools() has a 73-character description and send_confirmation has 71; every other schema runs 216 to 448.**

The static scan lists lookup_booking at 283, check_policy at 445, issue_voucher at 227, and then hold_seat at 73 and send_confirmation at 71. Those are the two tools that create a seat hold and send the customer a message. Neither description states when to call it or what it returns.

Run python3 run.py --show-tools and paste the full text of the hold_seat and send_confirmation descriptions.

**2. Your diff adds 8 tools to EXTRA_TOOLS, so tool_list() offers 17 schemas on every turn, up from the pack's 9.**

Your committed wire run in readout-trace.json shows 24543 input tokens over 4 turns and only 4 tools called: lookup_booking, get_flight_status, check_policy, cause_in_plain_words. Seven of your eight additions, among them reopen_stats and what_automation_will_not_do, were not called in that run. The diff adds no cache_control anywhere, and the same 17 schemas plus SYSTEM_PROMPT go out on all 4 turns with 0 tokens cached.

Run python3 run.py --tool-tax and paste its output next to the 24543 input-token figure.

**3. readout-trace.json records one run: 4 turns, 902 output tokens, 8.1s, and no cache reads or writes.**

That is the only wire evidence in the repository, and it is a single booking. There is no evals/cases.json, no bench-before.json or bench-after.json compare, and no second trace. Nothing here shows what a different model would change, since the loop already reaches its answer in 4 turns and the 0 cached tokens come from the request shape, not the model.

Run python3 bench.py --label before --stage 1 --runs 3 and then python3 bench.py --compare before after, and paste the compare output.

**4. TONE_ADDENDUM in agent.py is still 0 characters and the loop sends it unchanged on every messages.create call.**

run_agent builds system as runtime_preamble() + SYSTEM_PROMPT + TONE_ADDENDUM, so the customer-facing voice is whatever SYSTEM_PROMPT from support already says. PITCH.md has every field blank, including the Lever line. Nothing in the repository names which of cost, speed or intelligence you chose.

Paste the filled Lever line from PITCH.md and the one before-and-after number from python3 bench.py --compare that backs it.

**5. run_agent stops at MAX_TOOL_CALLS = 8 and returns text_of(response) with no escalation call and no message if the cap is hit.**

The while loop exits when turns reaches 8 even if stop_reason is still tool_use. text_of then returns the last non-empty text block, or an empty string if there is none. Your committed run used 4 turns, so nothing shows what the customer sees when a booking needs a ninth.

Run python3 run.py --all --trace and paste the totals footer, including the highest turn count across bookings.

## Your four answers

The four lines under `## Priya asked` in your PITCH.md are still empty. They
are one line each and they are not a coding job: cost, what happens when it is
wrong, who runs it in June, and what you left out. Whoever on your side is not
editing agent.py is the right person to write them, and they are the four
things I will ask about first.

## Before our next meeting

> Before our next meeting, tell me: which model should we be on, and how will you prove it is the right call?
>
> Priya Raghavan, Larkspur Airlines

Bring two things. A recommendation, and the measurement behind it. If the model is
not the problem, say so, and bring the number that shows it.

## What this review read

- `agent.py (557 lines)`
- `PITCH.md`
- `TEAM.md`
- `readout-trace.json`
- `readout.html (evidence block)`
- given files that differ from the shipped pack: `verify.py`, `eval_harness.py`, `bench.py`, `readout.py`, `setup.py`, `pod_sync.py`, `run.py`, `review.py`, `support/__init__.py`, `support/client.py`, `support/data.py`, `support/models.py`, `support/tools.py`, `support/trace.py`, `support/offline.py`, `support/mock_backend.py`, `support/mcp_client.py`, `support/mcp_server.py`, `support/mcp_selftest.py`, `support/access.py`, `support/keyscan.py`, `support/review.py`

Reviewer: `claude-sonnet-5-5`. Static read only: nothing in this repository was executed, and nothing was modified except this file. Larkspur Airlines is a fictional training scenario. Confidential, do not distribute.
