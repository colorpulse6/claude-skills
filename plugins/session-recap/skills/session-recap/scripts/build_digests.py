#!/usr/bin/env python3
"""Build compact conversation digests for NOTABLE sessions, for the LLM
"key decisions" pass. Reads <out>/sessions.json, writes <out>/digests/<id>.txt
and <out>/digests/index.json.

Each digest is the stripped USER/ASSISTANT prose (tool calls + large outputs
removed), capped — small enough to summarize cheaply.

Usage: build_digests.py --out ~/.claude/recaps
"""
import argparse, json, os, re

MAX_CHARS = 9000   # per-session digest cap
MAX_BLOCK = 1200   # per text block cap


def clean(text):
    text = re.sub(r"<command-[^>]*>.*?</command-[^>]*>", "", text, flags=re.S)
    text = re.sub(r"<command-[^>]*/?>", "", text)
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S)
    text = re.sub(r"<bash-[^>]*>.*?</bash-[^>]*>", "", text, flags=re.S)
    text = re.sub(r"<local-command[^>]*>.*?</local-command[^>]*>", "", text, flags=re.S)
    return text.strip()


def msg_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text")
    return ""


def is_tool_result(content):
    return isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in content)


def build(path):
    parts, used = [], 0
    for line in open(path, errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        t = o.get("type")
        if t not in ("user", "assistant") or o.get("isMeta") or o.get("isSidechain"):
            continue
        msg = o.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if t == "user":
            if is_tool_result(content):
                continue
            txt = clean(msg_text(content))
            if not txt or txt.startswith("/"):
                continue
            chunk = "USER: " + txt[:MAX_BLOCK]
        else:
            txt = clean(msg_text(content))
            if not txt:
                continue
            chunk = "ASSISTANT: " + txt[:MAX_BLOCK]
        if used + len(chunk) > MAX_CHARS:
            parts.append("...[truncated]...")
            break
        parts.append(chunk)
        used += len(chunk)
    return "\n\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="~/.claude/recaps")
    args = ap.parse_args()
    out = os.path.expanduser(args.out)
    digdir = os.path.join(out, "digests")
    os.makedirs(digdir, exist_ok=True)

    data = json.load(open(os.path.join(out, "sessions.json")))
    index = []
    for s in data["sessions"]:
        if not s["notable"]:
            continue
        digest = build(s["path"])
        if len(digest) < 40:
            continue
        with open(os.path.join(digdir, s["id"] + ".txt"), "w") as f:
            f.write(digest)
        index.append({
            "id": s["id"], "title": s["title"], "project": s["project"],
            "branch": s["branch"], "chars": len(digest),
            "prs": [p["num"] for p in s["prs"]], "commits": s["commits"],
            "files": s["file_count"],
        })
    json.dump(index, open(os.path.join(digdir, "index.json"), "w"), indent=2)
    print(f"wrote {len(index)} digests ({sum(i['chars'] for i in index)} chars) "
          f"-> {digdir}")


if __name__ == "__main__":
    main()
