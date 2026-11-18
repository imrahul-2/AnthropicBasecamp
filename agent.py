"""Larkspur disruption agent. This is the file you build.

It runs right now, and it is wrong in four places. The trace shows each one
before the code does, so read the trace first:

    python3 run.py K7PQ2M --trace

Where you edit:   grep -n '✏' agent.py   (six marks, one per place)
Steps and gates:  https://anthropicpartnerbasecamp.bts.com/
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Dict, List
from support import mock_backend
from support import (MODEL, SYSTEM_PROMPT, call_local, execute_tool, mcp_client,
                     new_session, next_available_day, record_tool_result,
                     runtime_preamble)

MAX_TOOL_CALLS = 8  # Larkspur's own build capped the loop here; then a human takes over.

TONE_ADDENDUM = ""                       # ✏️ Build 4, step 4.1, intelligence goal


def fare_rules(section: str) -> Any:
    """Return the Handbook text for one section of fare_rules_excerpt.md,
    matched by section number first, then by words in the title."""
    path = Path(__file__).resolve().parent / "data" / "americas" / "fare_rules_excerpt.md"
    sections, current = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            heading = line[4:].strip()
            m = re.match(r"^(\d+)\.\s*(.*)$", heading)
            current = {"number": m.group(1) if m else "", "title": m.group(2) if m else heading,
                       "lines": [line]}
            sections.append(current)
        elif current is not None:
            current["lines"].append(line)
    labels = ", ".join(f"{s['number']} ({s['title']})" for s in sections)
    query = re.sub(r"^section\s+", "", (section or "").strip().lower()).rstrip(".")
    if not query:
        return {"error": f"section is required. Available sections: {labels}."}
    for s in sections:
        if query == s["number"]:
            return "\n".join(s["lines"]).strip()
    for s in sections:
        if query in s["title"].lower():
            return "\n".join(s["lines"]).strip()
    return {"error": f"No section matches {section!r}. Available sections: {labels}."}


_DATA = Path(__file__).resolve().parent / "data" / "americas"


def _policy() -> Dict[str, Any]:
    return json.loads((_DATA / "disruption_policy.json").read_text(encoding="utf-8"))


def cause_in_plain_words(cause_code: str, language: str = "en") -> Any:
    """The customer-facing wording for a cause code, from cause_labels_customer."""
    labels = _policy()["cause_labels_customer"]
    code = (cause_code or "").strip().upper()
    if code not in labels:
        return {"error": f"Unknown cause_code {cause_code!r}. Use one of: {', '.join(labels)}."}
    lang = (language or "en").strip().lower()
    if lang not in labels[code]:
        return {"error": f"No {lang!r} wording. Available: {', '.join(labels[code])}."}
    return {"cause_code": code, "language": lang, "customer_wording": labels[code][lang]}


def care_entitlements(cause_code: str, status: str, delay_minutes: int = 0) -> Any:
    """What care (meal, hotel, ground) applies while waiting: the policy row's
    care block plus Handbook section 6."""
    policy = _policy()
    code = (cause_code or "").strip().upper()
    status = (status or "").strip().upper()
    if code not in policy["cause_classes"]:
        return {"error": f"Unknown cause_code {cause_code!r}. Use one of: {', '.join(policy['cause_classes'])}."}
    if status == "CANCELLED":
        band = "CXL"
    elif status == "DIVERTED":
        band = "DIV"
    elif status in ("ON_TIME", "DELAYED"):
        band = next((b["band"] for b in policy["delay_bands"]
                     if b["band"] not in ("CXL", "DIV") and b["min_minutes"] <= int(delay_minutes or 0)
                     and (b["max_minutes"] is None or int(delay_minutes or 0) <= b["max_minutes"])), None)
    else:
        return {"error": "status must be one of ON_TIME, DELAYED, CANCELLED, DIVERTED."}
    prefix = "UNC" if policy["cause_classes"][code] == "uncontrollable" else "CTL"
    row = next((r for r in policy["rows"] if r["policy_row_id"] == f"{prefix}-{band}"), None)
    if row is None:
        return {"error": f"No policy row for {prefix}-{band}."}
    return {"policy_row_id": row["policy_row_id"], "care": row["care"],
            "explainer": row.get("explainer_en"), "handbook_section_6": fare_rules("6")}


def reopen_stats(intent_label: str = "") -> Any:
    """How often each kind of problem came back within 72 hours, from the
    eight human-handled transcripts. Small sample: say so."""
    rows = [json.loads(l) for l in
            (_DATA / "transcripts_sample.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    want = (intent_label or "").strip().lower()
    groups: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        g = groups.setdefault(r["intent_label"], {"conversations": 0, "reopened_within_72h": 0, "reasons": []})
        g["conversations"] += 1
        if r.get("reopened_within_72h"):
            g["reopened_within_72h"] += 1
            if r.get("reopen_reason"):
                g["reasons"].append(r["reopen_reason"])
    if want:
        groups = {k: v for k, v in groups.items() if want in k.lower()}
        if not groups:
            return {"error": f"No transcripts match {intent_label!r}.",
                    "available": sorted({r["intent_label"] for r in rows})}
    return {"sample_size": len(rows),
            "caveat": "8 human-handled transcripts out of 600 read; a sample, not a rate.",
            "by_intent": groups,
            "overall_reopened": sum(1 for r in rows if r.get("reopened_within_72h"))}


def next_available_day(origin: str, dest: str, date: str, cabin: str = "Y") -> Any:
    """Wraps the given next_available_day so 'nothing open' is said in words,
    not returned as a bare None."""
    found = mock_backend.earliest_alternative_date(origin, dest, date, cabin)
    if not found:
        return {"result": None, "message": f"No open {cabin} seat from {origin} to {dest} on or after "
                                           f"{date} in the schedule I can see."}
    return {"earliest_date": found, "for_passengers": 1}


def _now():
    return mock_backend.FIXTURE_CLOCK


def departures_in_window(airport: str, date: str, from_time: str = "", to_time: str = "") -> Any:
    """Flights leaving one airport on one date between two local times (HH:MM).
    On the sample data's 'today', from_time defaults to the sample 'now'."""
    ap = (airport or "").strip().upper()
    if len(ap) != 3 or not re.match(r"^\d{4}-\d{2}-\d{2}$", date or ""):
        return {"error": "airport must be a 3-letter code (e.g. DEN) and date YYYY-MM-DD."}
    now = _now()
    if not from_time and date == now.strftime("%Y-%m-%d"):
        from_time = now.strftime("%H:%M")
    rows = [r for r in mock_backend.load_flights()
            if r["origin"] == ap and r["date"] == date
            and (not from_time or r["sched_dep_local"] >= from_time)
            and (not to_time or r["sched_dep_local"] <= to_time)]
    rows.sort(key=lambda r: r["sched_dep_local"])
    keep = ("flight_no", "dest", "sched_dep_local", "sched_arr_local", "status", "delay_min",
            "seats_left_Y", "seats_left_J", "remarks")
    return {"airport": ap, "date": date, "from_time": from_time or None, "to_time": to_time or None,
            "as_of": now.isoformat(), "departures": [{k: r[k] for k in keep} for r in rows]}


def seats_left(flight_no: str, date: str, party_size: int = 1) -> Any:
    """Free seats in each cabin on one flight, and whether the whole party fits."""
    row = next((r for r in mock_backend.load_flights()
                if r["flight_no"] == (flight_no or "").strip().upper() and r["date"] == date), None)
    if row is None:
        return {"error": f"No flight {flight_no} on {date} in the schedule."}
    n = int(party_size or 1)
    return {"flight_no": row["flight_no"], "date": date, "status": row["status"],
            "seats_left_Y": row["seats_left_Y"], "seats_left_J": row["seats_left_J"],
            "party_size": n, "party_fits_Y": row["seats_left_Y"] >= n,
            "party_fits_J": row["seats_left_J"] >= n}


def ground_stop_status(airport: str) -> Any:
    """Ground-stop remarks for an airport on the sample 'today', with the sample 'now'."""
    ap = (airport or "").strip().upper()
    now = _now()
    today = now.strftime("%Y-%m-%d")
    notes = [{"flight_no": r["flight_no"], "origin": r["origin"], "dest": r["dest"],
              "status": r["status"], "remark": r["remarks"]}
             for r in mock_backend.load_flights()
             if r["date"] == today and "ground stop" in r["remarks"].lower()
             and ap in (r["origin"], r["dest"], *re.findall(r"\b[A-Z]{3}\b", r["remarks"]))]
    return {"airport": ap, "now": now.isoformat(), "ground_stop_remarks": notes,
            "note": "Read the stop window in each remark against 'now'. No remark means no ground stop on record."}


def hold_time_left(hold_id: str) -> Any:
    """Minutes left on a seat hold, measured against the sample 'now'."""
    hold = mock_backend._holds.get((hold_id or "").strip())
    if hold is None:
        return {"error": f"No active hold {hold_id!r}. It may have been confirmed or never placed."}
    left = (hold["expires_at"] - _now()).total_seconds() / 60
    return {"hold_id": hold_id, "option_id": hold["option_id"], "minutes_left": max(0, round(left, 1)),
            "expired": left <= 0, "expires_at": hold["expires_at"].isoformat()}


def what_automation_will_not_do() -> Any:
    """Handbook section 7: what the chat is not allowed to do."""
    return fare_rules("7")


EXTRA_TOOLS: List[Dict[str, Any]] = [    # ✏️ Build 2, step 2.1: schemas for the tools you add
    {
        "name": "reopen_stats",
        "description": (
            "Answer 'is this problem going to come back?' from real history. Use when the "
            "customer asks whether their issue will recur or need a second contact. Returns, "
            "from eight human-handled transcripts, how many conversations of each kind of "
            "problem were reopened within 72 hours and why. It is a small sample, not a "
            "rate: say so when you quote it. None of the nine tools has this history."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "intent_label": {"type": "string", "description": (
                    "Optional kind of problem to filter on, e.g. rebook_after_cancellation, "
                    "compensation_hotel_request, refund_vs_credit. Leave empty for all.")},
            },
        },
    },
    {
        "name": "care_entitlements",
        "description": (
            "Answer 'do I get a meal or a hotel while I wait?'. Use when the customer asks what "
            "care they are owed during a delay, cancellation or diversion. Needs cause_code and "
            "status from get_flight_status. Returns the policy row's meal, hotel and ground "
            "amounts plus Handbook section 6, so quote those and never invent amounts. Unlike check_policy, which resolves the whole "
            "decision for a booking, this answers only the care question."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cause_code": {"type": "string", "enum": ["WX", "ATC", "MX", "CREW", "SEC"],
                               "description": "Cause code from get_flight_status"},
                "status": {"type": "string", "enum": ["ON_TIME", "DELAYED", "CANCELLED", "DIVERTED"],
                           "description": "Flight status from get_flight_status"},
                "delay_minutes": {"type": "integer", "description": "Delay in minutes from get_flight_status; 0 if cancelled or diverted"},
            },
            "required": ["cause_code", "status"],
        },
    },
    {
        "name": "cause_in_plain_words",
        "description": (
            "Answer 'why was my flight cancelled?' in words a customer can repeat. Use when "
            "explaining a cause to the customer: turns a code like WX into approved wording "
            "such as 'weather', in English or Spanish. Needs the cause_code from "
            "get_flight_status. Use this wording instead of the raw code that get_flight_status and check_policy return."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cause_code": {"type": "string", "enum": ["WX", "ATC", "MX", "CREW", "SEC"],
                               "description": "Cause code from get_flight_status"},
                "language": {"type": "string", "enum": ["en", "es"],
                             "description": "Customer's language from lookup_booking; default en"},
            },
            "required": ["cause_code"],
        },
    },
    {
        "name": "departures_in_window",
        "description": (
            "Answer 'what is still leaving this airport this afternoon?'. Use when the customer "
            "wants options out of an airport in a time window rather than for their own booking. "
            "Returns flights from flights.csv for one airport and date, between two local times, "
            "with status, delay and free seats; an empty list means nothing leaves in that window. "
            "Unlike search_alternatives, it is not tied to a booking. On the sample data's today, "
            "the start defaults to now."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "airport": {"type": "string", "description": "Three-letter departure airport code, e.g. DEN"},
                "date": {"type": "string", "description": "Local date, ISO format YYYY-MM-DD, e.g. 2025-05-08"},
                "from_time": {"type": "string", "description": "Earliest local departure, 24-hour HH:MM, e.g. 12:00. Optional"},
                "to_time": {"type": "string", "description": "Latest local departure, 24-hour HH:MM, e.g. 18:00. Optional"},
            },
            "required": ["airport", "date"],
        },
    },
    {
        "name": "seats_left",
        "description": (
            "Answer 'is there room on that flight for all of us?'. Use before offering or holding "
            "a flight for a party of more than one. Returns the free seats in each cabin (Y main, "
            "J first) for one flight and date, and whether the whole party fits. Unlike "
            "search_alternatives, which answers for one passenger, this checks the party size."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "flight_no": {"type": "string", "description": "Flight number, e.g. LK411"},
                "date": {"type": "string", "description": "Local departure date, ISO format YYYY-MM-DD"},
                "party_size": {"type": "integer", "description": "Number of passengers travelling together; default 1"},
            },
            "required": ["flight_no", "date"],
        },
    },
    {
        "name": "ground_stop_status",
        "description": (
            "Answer 'is this airport still stopped, and until when?'. Use when a customer asks "
            "whether a ground stop or weather hold is still in force. Returns the ground-stop "
            "remarks on record for the airport and the current time, so compare the stated window "
            "with now and never guess an end time. get_flight_status covers one flight; this covers the airport."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "airport": {"type": "string", "description": "Three-letter airport code, e.g. DEN"},
            },
            "required": ["airport"],
        },
    },
    {
        "name": "hold_time_left",
        "description": (
            "Answer 'how long do I have before this seat is released?'. Use after hold_seat when "
            "the customer asks how much time is left to confirm. Returns minutes remaining on "
            "the hold and whether it has expired. hold_seat creates a hold; this only reads the time left."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "hold_id": {"type": "string", "description": "Hold id returned by hold_seat, e.g. HOLD-1A2B3C"},
            },
            "required": ["hold_id"],
        },
    },
    {
        "name": "what_automation_will_not_do",
        "description": (
            "Answer 'can you just cancel the whole trip for me?' and any request that may be "
            "outside what the chat may do. Use before refusing or promising something unusual. "
            "Takes no input; returns Handbook section 7, what chat automation will not do, "
            "which tells you when to escalate_to_human instead."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
]
LOCAL_TOOLS: Dict[str, Any] = {          # ✏️ Build 2, step 2.1: the functions behind them
    "reopen_stats": reopen_stats,
    "care_entitlements": care_entitlements,
    "cause_in_plain_words": cause_in_plain_words,
    "departures_in_window": departures_in_window,
    "seats_left": seats_left,
    "ground_stop_status": ground_stop_status,
    "hold_time_left": hold_time_left,
    "what_automation_will_not_do": what_automation_will_not_do,
}


def text_of(response) -> str:
    """Given. The last non-empty text block, never content[0]."""
    texts = [b.text for b in response.content if getattr(b, "type", None) == "text" and b.text]
    return texts[-1] if texts else ""


def tool_results(response) -> List[Dict[str, Any]]:
    """Given. Runs every tool_use block and packages the results the way the
    API expects them back. A tool can live in three places: the MCP server,
    LOCAL_TOOLS, or support/tools.py."""
    # three branches, no try/except in this file: mcp_client.call_remote() and
    # support.call_local() answer with an error dict instead of raising, and both
    # record what came back on the trace
    results = []
    for block in response.content:
        if getattr(block, "type", None) != "tool_use":
            continue
        if block.name in mcp_client.tool_names:
            output = mcp_client.call_remote(block.name, block.input)
        elif block.name in LOCAL_TOOLS:
            output = call_local(LOCAL_TOOLS[block.name], block.name, block.input)
        else:
            output = execute_tool(block.name, block.input)
        results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": str(output),
        })
    return results


def run_agent(pnr: str, last_name: str, message: str) -> str:            # ✏️ Build 1, step 1.2
    """Run the tool loop until Claude stops asking for tools. Return its final text."""
    client, tracer = new_session()
    tools = tool_list()
    messages = [
        {"role": "user", "content": f"PNR {pnr}, last name {last_name}. {message}"},
    ]

    response = client.messages.create(
        model=MODEL, max_tokens=4096, system=runtime_preamble() + SYSTEM_PROMPT + TONE_ADDENDUM,
        thinking={"type": "adaptive"}, tools=tools, messages=messages,
    )

    turns = 1
    while response.stop_reason == "tool_use" and turns < MAX_TOOL_CALLS:
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results(response)})
        response = client.messages.create(
            model=MODEL, max_tokens=4096, system=runtime_preamble() + SYSTEM_PROMPT + TONE_ADDENDUM,
            thinking={"type": "adaptive"}, tools=tools, messages=messages,
        )
        turns += 1

    return text_of(response)


def tool_list() -> List[Dict[str, Any]]:                   # ✏️ Build 2, step 2.2
    """Given. Exactly what Claude is offered on every turn; run.py --show-tools
    prints this list."""
    return build_tools() + EXTRA_TOOLS + mcp_client.tools()


# ──────────────────────────────────────────────────────────────────────────────
# Below this line: what Claude is told about each tool. Step 1.3.
# The functions these describe are written and correct, in support/tools.py.
# ──────────────────────────────────────────────────────────────────────────────
def build_tools() -> List[Dict[str, Any]]:                 # ✏️ Build 1, step 1.3
    """Anthropic-shaped schemas: name, description, input_schema. What Claude is
    told about each of the nine tools, and all it is ever told."""
    return [
        {
            "name": "lookup_booking",
            "description": (
                "Retrieve a Larkspur reservation from Altura by confirmation code (PNR) "
                "and the passenger's last name. Both are required to prevent a lookup on "
                "a guessed PNR. Returns fare family, loyalty tier, the segment that needs "
                "attention, and any group/partner/minor/SSR flags relevant to scope."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}, "last_name": {"type": "string"}},
                "required": ["pnr", "last_name"],
            },
        },
        {
            "name": "get_flight_status",
            "description": (
                "Look up a Larkspur or Larkspur Link flight's current OpsFeed status for "
                "one local date: status, delay minutes, and cause. Use this before telling "
                "a customer anything about a flight's timing; never state it from memory."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "flight_no": {"type": "string"},
                    "date": {"type": "string", "description": "Local departure date in ISO format YYYY-MM-DD, e.g. 2025-05-08"},
                },
                "required": ["flight_no", "date"],
            },
        },
        {
            "name": "search_alternatives",
            "description": (
                "Find ranked rebooking options (flights, date, arrival time, fare difference) "
                "for the disrupted segment on a booking. Use after lookup_booking and "
                "get_flight_status confirm the flight is cancelled, diverted or badly delayed, "
                "and before offering the customer any alternative. Each option has an "
                "option_id; pass that to hold_seat or check_policy. Never invent options."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string", "description": "Confirmation code (PNR) of the booking, as returned by lookup_booking"}},
                "required": ["pnr"],
            },
        },
        {
            "name": "check_policy",
            "description": (
                "Resolve what Larkspur owes this customer for the disruption: rebooking "
                "waiver, refund path, meal/hotel/ground care, goodwill eligibility and cap, "
                "and any escalation triggers. cause_code, delay_minutes and status describe "
                "what get_flight_status told you; fare_family, loyalty_tier and whether this "
                "is overnight are looked up from the booking, not asked of you. Every "
                "response carries a policy_row_id. Cite it if you reference this decision "
                "again."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string"},
                    "cause_code": {"type": "string", "enum": ["WX", "ATC", "MX", "CREW", "SEC"]},
                    "delay_minutes": {"type": "integer"},
                    "status": {"type": "string", "enum": ["ON_TIME", "DELAYED", "CANCELLED", "DIVERTED"]},
                    "wait_minutes_for_alternative": {"type": "integer"},
                    "chosen_option_id": {"type": "string"},
                },
                "required": ["pnr", "cause_code", "delay_minutes", "status"],
            },
        },
        {
            "name": "hold_seat",
            "description": "Place a 15-minute hold on one alternative. Reversible. It simply expires.",
            "input_schema": {
                "type": "object",
                "properties": {"option_id": {"type": "string"}, "pnr": {"type": "string"}},
                "required": ["option_id", "pnr"],
            },
        },
        {
            "name": "confirm_rebooking",
            "description": (
                "Finalize a held seat. Irreversible. Requires a confirmation_token that "
                "only the customer's own Confirm-click can produce. You cannot supply it "
                "yourself, and 'the customer said yes' in chat does not substitute for it."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"hold_id": {"type": "string"}, "confirmation_token": {"type": "string"}},
                "required": ["hold_id", "confirmation_token"],
            },
        },
        {
            "name": "issue_voucher",
            "description": (
                "Issue a meal, ground, hotel, or goodwill voucher. Auto-approves within the "
                "policy's threshold for that type; above it, returns a pending status for a "
                "human. It does not fail. Always pass the policy_row_id that made it eligible."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "voucher_type": {"type": "string", "enum": ["meal", "ground", "hotel", "goodwill"]},
                    "amount_usd": {"type": "number"},
                    "pnr": {"type": "string"},
                    "policy_row_id": {"type": "string"},
                },
                "required": ["voucher_type", "amount_usd", "pnr", "policy_row_id"],
            },
        },
        {
            "name": "escalate_to_human",
            "description": (
                "Hand this conversation to a human, with your reasoning attached. Use for "
                "groups, partner segments, unaccompanied minors, refunds, or anything else "
                "out of scope. This is the correct outcome for those cases, not a failure."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string"}, "reason": {"type": "string"},
                    "summary_for_human": {"type": "string"}, "queue": {"type": "string"},
                },
                "required": ["pnr", "reason", "summary_for_human"],
            },
        },
        {
            "name": "send_confirmation",
            "description": "Send the customer a written confirmation of what was just done. Benign.",
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}, "message": {"type": "string"}},
                "required": ["pnr", "message"],
            },
        },
    ]
