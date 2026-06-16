"""
TMLR author-count reporter, coded up using Opus 4.8. 

Log in with your OpenReview account; this prints a comma-separated list giving
the number of authors on each paper YOU submitted to TMLR (Transactions on
Machine Learning Research) during the current calendar year.

Your identity is taken from the authenticated session, so you are not asked for
a profile id -- just your login email and password.

Setup:
    pip install openreview-py          # requires Python 3.9+
Run:
    python tmlr_author_counts.py

Notes:
  * TMLR is hosted on OpenReview's API v2 (https://api2.openreview.net).
  * Papers are matched by authorship: a paper counts if you are listed among its
    authors, whether or not you were the one who submitted it. The query is
    permission-aware, so your own under-review double-blind papers are included.
  * "Submitted in the current calendar year" uses each paper's submission
    timestamp (note.cdate) in UTC. Swap timezone.utc -> None for local time.
"""

import sys
import json
import base64
import getpass
from datetime import datetime, timezone

import openreview          # pip install openreview-py
import openreview.api      # API v2 client lives here


# Every paper submitted to TMLR carries this invitation on its submission note.
TMLR_SUBMISSION_INVITATION = "TMLR/-/Submission"


def note_invitations(note):
    """Return a note's invitation id(s) as a list (v2 uses .invitations)."""
    invs = getattr(note, "invitations", None)
    if invs:
        return invs
    inv = getattr(note, "invitation", None)   # v1 fallback
    return [inv] if inv else []


def author_identifiers(profile):
    """All tilde-ids tied to one profile (a person may have several names).

    Profile.content can come back as None (e.g. the sparse profile cached at
    login), so guard it -- the canonical id alone is enough to find papers.
    """
    ids = {profile.id} if getattr(profile, "id", None) else set()
    content = getattr(profile, "content", None) or {}
    for name in content.get("names", []) or []:
        if name and name.get("username"):
            ids.add(name["username"])
    return ids


def _tilde_from_token(token):
    """Pull the first ~Tilde_Id out of a JWT auth token's payload."""
    if not token:
        return None
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)          # pad base64
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()))
    except Exception:
        return None
    stack = [payload]                                          # walk the JSON
    while stack:
        cur = stack.pop()
        if isinstance(cur, str) and cur.startswith("~") and cur[-1:].isdigit():
            return cur
        if isinstance(cur, dict):
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


def session_user_id(client):
    """The logged-in user's ~Tilde_Id, read from the session (no prompt).

    The client caches a profile/user at login; if not, recover the id from the
    auth token. Only values that look like a tilde id are accepted.
    """
    cached = getattr(client, "profile", None)
    cid = getattr(cached, "id", None)
    if isinstance(cid, str) and cid.startswith("~"):
        return cid

    user = getattr(client, "user", None)
    if isinstance(user, dict):
        uid = user.get("id") or (user.get("profile") or {}).get("id")
        if isinstance(uid, str) and uid.startswith("~"):
            return uid

    return _tilde_from_token(getattr(client, "token", None))


def fetch_profile(client, tilde_id):
    """Full Profile for a tilde id via search_profiles(ids=[...]), or None."""
    try:
        profiles = client.search_profiles(ids=[tilde_id])
    except Exception:
        return None
    return profiles[0] if profiles else None


def main():
    # --- 1. Log in -------------------------------------------------------------
    login_email = input("OpenReview login email: ").strip()
    password = getpass.getpass("OpenReview password: ")

    try:
        client = openreview.api.OpenReviewClient(
            baseurl="https://api2.openreview.net",
            username=login_email,
            password=password,
        )
    except openreview.OpenReviewException as err:
        sys.exit(f"Login failed: {err}")

    # --- 2. Figure out who you are (from the session, not by asking) -----------
    uid = session_user_id(client)
    if not uid:
        uid = input("Couldn't read your identity from the session. "
                    "Enter your ~Tilde_Id: ").strip()

    profile = fetch_profile(client, uid)
    my_tilde_ids = author_identifiers(profile) if profile is not None else {uid}
    if not my_tilde_ids:
        sys.exit("Could not determine your OpenReview profile id.")
    print(f"Analyzing TMLR submissions for {uid}")

    # --- 3. Collect your TMLR submissions --------------------------------------
    # content={'authorids': ...} returns your papers across all venues
    # (permission-aware); keep the TMLR submissions. get_all_notes() paginates.
    tmlr_notes = {}
    for tilde_id in my_tilde_ids:
        for note in client.get_all_notes(content={"authorids": tilde_id}):
            if any(inv.startswith(TMLR_SUBMISSION_INVITATION)
                   for inv in note_invitations(note)):
                tmlr_notes[note.id] = note

    # --- 4. Filter to the current calendar year and count authors --------------
    current_year = datetime.now(timezone.utc).year
    counts = []
    for note in sorted(tmlr_notes.values(), key=lambda n: n.cdate or 0):
        submitted_ms = note.cdate if note.cdate is not None else note.tcdate
        if submitted_ms is None:
            continue
        submitted = datetime.fromtimestamp(submitted_ms / 1000, tz=timezone.utc)
        if submitted.year != current_year:
            continue

        authorids = (note.content or {}).get("authorids", {})
        num_authors = len(authorids.get("value", []) if isinstance(authorids, dict) else [])
        counts.append(num_authors)

        title_field = (note.content or {}).get("title", {})
        title = title_field.get("value", "(title hidden)") if isinstance(title_field, dict) else "(title hidden)"
        print(f"[{submitted.date()}] {num_authors:>2} authors  {title}")

    print(f"\n{len(counts)} TMLR submission(s) in {current_year}")

    # --- 5. Final labeled output, last line --------------------------------
    print(f"\nNumber of authors: {','.join(str(c) for c in counts)}")


if __name__ == "__main__":
    main()