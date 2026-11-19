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

**1. agent.py declares EXTRA_TOOLS with 8 schemas, so the model chooses among 17 tools on every turn, 9 of them from the pack.**

The static scan counts 17 tool schemas, 8 with local executors: reopen_stats, care_entitlements, cause_in_plain_words, departures_in_window, seats_left, ground_stop_status, hold_time_left, what_automation_will_not_do. The last committed wire run took 4 API turns and 6 tool calls, and called only one of the eight additions, cause_in_plain_words. A larger model changes none of that routing surface.

Run python3 run.py --show-tools and python3 run.py --tool-tax and paste the output.

**2. readout-trace.json shows 26194 tokens in, 1153 out, 0 cache reads and 0 cache writes across 4 API turns, and agent.py has no cache_control.**

The input side is about 23 times the output side on a single booking. The static scan finds no cache_control anywhere in agent.py, so the 17 schemas and the system prompt are paid for at full input price on every turn. Which of those tokens are tool definitions and which are conversation has not been measured anywhere in the repository.

Run python3 run.py --tool-tax and paste the per-tool token figures next to the 26194 total.

**3. The eval suite is missing: evals/cases.json does not exist, and the only evidence is a single committed wire run.**

readout-trace.json records one run: 6 tool calls, 13.2s, thinking seen on the wire. Gates 1.2, 1.3, 1.4, 2.1 and 2.2 are banked in readout.html, and 3.1 and 4.1 are not. Nothing in the repository tests a booking shape where the answer is wrong, so no pass rate exists for any model.

Run python3 eval_harness.py and paste the pass and fail summary.

**4. TONE_ADDENDUM in agent.py is 0 characters, and the diff changes no system prompt text.**

run_agent builds its system prompt as runtime_preamble() + SYSTEM_PROMPT + TONE_ADDENDUM, and the third piece is empty. The diff adds 413 lines, and the whole of that is tool schemas and executors. The wording the customer receives was not touched by any line this team wrote.

Run python3 run.py K7PQ2M --trace and paste the final customer-facing message.

**5. PITCH.md is blank and bench-after.json is not in the repository, so no before and after number has been committed.**

The Number, Safety check and Still broken lines are empty, and the Lever line still reads cost | speed | intelligence. The one measured figure is the 26194-in, 1153-out token count from readout-trace.json, and nothing has been measured against it. With no baseline, nobody can say whether model choice or a trimmed tool list moves cost, and Priya's question has nothing to rest on.

Run python3 bench.py --label before --stage 1 --runs 3 and paste the totals line.

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

- `agent.py (627 lines)`
- `PITCH.md`
- `TEAM.md`
- `readout-trace.json`
- `readout.html (evidence block)`
- given files that differ from the shipped pack: `verify.py`, `eval_harness.py`, `bench.py`, `readout.py`, `setup.py`, `pod_sync.py`, `run.py`, `review.py`, `support/__init__.py`, `support/client.py`, `support/data.py`, `support/models.py`, `support/tools.py`, `support/trace.py`, `support/offline.py`, `support/mock_backend.py`, `support/mcp_client.py`, `support/mcp_server.py`, `support/mcp_selftest.py`, `support/access.py`, `support/keyscan.py`, `support/review.py`

Reviewer: `claude-sonnet-5-5`. Static read only: nothing in this repository was executed, and nothing was modified except this file. Larkspur Airlines is a fictional training scenario. Confidential, do not distribute.
