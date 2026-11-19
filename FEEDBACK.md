# Client review: Larkspur disruption-care agent

**To:** Room 6  
**From:** Larkspur client review agent, on behalf of Priya Raghavan  
**Re:** the disruption-care agent you walked us through in our last session  
**Generated:** 2026-11-19 04:39

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

**1. agent.py, build_tools(): send_confirmation still carries the 71-character description 'Send the customer a written confirmation of what was just done. Benign.'**

It is the shortest of the nine descriptions by 145 characters. The other eight run 216 to 739. Your diff did not touch it. It says nothing about when to call it or what goes in 'message'.

Run python3 run.py --show-tools and paste the send_confirmation entry with a one-line rule for when the agent calls it.

**2. agent.py, run_agent(): your diff changed the loop to append response.content and return text_of(response) from the final turn.**

The assistant turn now carries the full content blocks, which keeps the tool_use ids the next tool_result refers to. The return value is the last response's text. You have no trace showing a multi-tool booking passing through it. The committed readout-trace.json is one run: 4 API turns, 3 tool calls.

Run python3 run.py --all --trace and paste the totals footer.

**3. agent.py, build_tools(): search_alternatives went from description 'search' to 739 characters, and the date in get_flight_status now demands YYYY-MM-DD.**

You also rewrote hold_seat to say 'never hold on a guess or to compare options'. These are edits to what the model is told. readout-trace.json shows the last committed run calling lookup_booking, get_flight_status and check_policy, then stopping. search_alternatives and hold_seat do not appear in it.

Run python3 run.py K7PQ2M --trace and paste the tool sequence so the rewritten descriptions can be seen firing.

**4. readout-trace.json: 14505 tokens in, 0 cache read, 0 written, hit ratio None, and cache_control appears nowhere in agent.py.**

Every turn resends runtime_preamble() + SYSTEM_PROMPT + TONE_ADDENDUM plus nine tool schemas. TONE_ADDENDUM is 0 characters, so that part of the prompt is still the shipped one. Priya's question about a bigger model has to be answered against a bill where 14505 input tokens went through one 10.7s run with no caching.

Run python3 run.py --tool-tax and paste its output next to the 14505 in figure.

**5. PITCH.md is blank, there is no evals/cases.json, and bench.py output is absent, so nothing in the repository says what your changes bought.**

The one wire run in readout-trace.json postdates your diff. It has no before to sit against. Without a stage-1 comparison and a case list, a model name has no number to be weighed against. MAX_TOOL_CALLS is 8 and the committed run used 4 turns, so the cap has not been tested either.

Run python3 bench.py --label before --stage 1 --runs 3, then the same with --label after, then python3 bench.py --compare before after, and paste the compare output.

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

- `agent.py (264 lines)`
- `PITCH.md`
- `TEAM.md`
- `readout-trace.json`
- given files that differ from the shipped pack: `verify.py`, `eval_harness.py`, `bench.py`, `readout.py`, `setup.py`, `pod_sync.py`, `run.py`, `review.py`, `support/__init__.py`, `support/client.py`, `support/data.py`, `support/models.py`, `support/tools.py`, `support/trace.py`, `support/offline.py`, `support/mock_backend.py`, `support/mcp_client.py`, `support/mcp_server.py`, `support/mcp_selftest.py`, `support/access.py`, `support/keyscan.py`, `support/review.py`

Reviewer: `claude-sonnet-5-5`. Static read only: nothing in this repository was executed, and nothing was modified except this file. Larkspur Airlines is a fictional training scenario. Confidential, do not distribute.
