"""report.py, notify.py and the agent CLI end to end (task T4 tests 9, 10)."""
import datetime as dt
import json
import os
import subprocess
import sys

import agent
from conftest import PARTS, STARTER_NEEDS
from model import Config, Need, Offer, Release, load_needs
from notify import MAX_CHARS, telegram, truncate
from plan import Alert, plan_need
from report import render_markdown, render_telegram

TODAY = dt.date(2026, 10, 9)
AGENT = os.path.join(PARTS, "agent.py")


# ---------------------------------------------------------------- report

def test_dry_run_report_for_starter_needs_has_need_order_by_and_adapter_table(capsys):
    rc = agent.run(["--dry-run", "--offline", "--needs", STARTER_NEEDS, "--today", "2026-10-09",
                    "--state", "/nonexistent/state.json"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "| N001 |" in out and "M4 x 16" in out
    assert "2026-10-09" in out                       # order_by for r2a: Sat 11 Oct -> Fri 9 Oct
    assert "## Adapters" in out
    for name in ("comet", "vikiwat", "tme", "mouser", "amazon_de", "bauhaus", "3dcolour"):
        assert f"| {name} |" in out
    assert "disabled" in out                         # tme / mouser without keys
    assert "Telegram text that would be sent" in out
    assert not os.path.exists("/nonexistent/state.json")


def test_markdown_shows_check_price_by_hand_for_link_only_best():
    cfg = load_needs(STARTER_NEEDS)
    need = cfg.needs[0]
    link = Offer(need.id, "amazon_de", "amazon.de (check price by hand)", "https://www.amazon.de/dp/x",
                 None, lead_days=5, confidence="low")
    line = plan_need(cfg, need, [link], TODAY)
    md = render_markdown(cfg, [line], {"amazon_de": {"kind": "link", "state": "ok", "fails": 0}}, [], TODAY, "now")
    assert "check price by hand" in md
    assert "| amazon_de | link | ok |" in md


def test_telegram_text_empty_when_nothing_to_say_and_digest_lists_next_three():
    cfg = load_needs(STARTER_NEEDS)
    lines = [plan_need(cfg, n, [], TODAY) for n in cfg.needs]
    assert render_telegram(lines, {}, [], TODAY, digest=False) == ""
    txt = render_telegram(lines, {"tme": {"state": "disabled"}}, [], TODAY, digest=True, report_url="https://x/REPORT.md")
    assert "Next to order" in txt and "N001" in txt and "tme disabled" in txt and "https://x/REPORT.md" in txt


def test_telegram_text_for_30_needs_with_alerts_fits_3500_chars():
    rels = {"r2a": Release("r2a", dt.date(2026, 10, 16))}
    needs = [Need(id=f"N{i:03d}", what=f"part number {i} with a fairly long descriptive name", qty=1, release="r2a",
                  queries={"comet": "x"}) for i in range(1, 31)]
    cfg = Config(2, rels, ["comet"], {"comet": 1}, needs)
    lines = [plan_need(cfg, n, [], TODAY) for n in needs]
    alerts = [Alert("ORDER_SOON", n.id, f"{n.id} order by 2026-10-13 (3 d left) · comet 12.34 € · {n.what} " + "x" * 80)
              for n in needs]
    alerts += [Alert("NEW_BEST", n.id, f"{n.id} best: comet 12.34 € · {n.what}" + "y" * 60) for n in needs]
    raw = render_telegram(lines, {}, alerts, TODAY, digest=True, report_url="https://github.com/x/REPORT.md")
    assert len(raw) > MAX_CHARS
    sent = truncate(raw)
    assert len(sent) <= MAX_CHARS
    assert "… +" in sent and sent.endswith("more")


# ---------------------------------------------------------------- notify

def test_truncate_keeps_short_text():
    assert truncate("hello") == "hello"


def test_telegram_falls_back_to_stdout_without_secrets(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    import io
    buf = io.StringIO()
    assert telegram("ping", out=buf) is False
    assert "ping" in buf.getvalue() and "disabled" in buf.getvalue()


# ---------------------------------------------------------------- agent CLI

def test_invalid_needs_exit_2(tmp_path, capsys):
    bad = tmp_path / "needs.yaml"
    bad.write_text("releases: [{id: r1, date: 2026-10-16}]\nsuppliers: {default_lead_days: {comet: 1}}\n"
                   "needs: [{id: N001, what: x, qty: 1, for: r9}]\n", encoding="utf-8")
    rc = agent.run(["--dry-run", "--offline", "--needs", str(bad)])
    assert rc == 2
    err = capsys.readouterr().err
    assert err.startswith("needs.yaml invalid:") and "N001" in err and "r9" in err


def test_full_run_writes_state_and_report_and_is_quiet_second_time(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    state = tmp_path / "state.json"
    report = tmp_path / "REPORT.md"
    args = ["--offline", "--needs", STARTER_NEEDS, "--state", str(state), "--report", str(report), "--today", "2026-10-09"]
    assert agent.run(args) == 0
    out1 = capsys.readouterr().out
    assert state.exists() and report.exists()
    data = json.loads(state.read_text(encoding="utf-8"))
    assert data["needs"]["N001"]["order_by"] == "2026-10-09"
    assert data["needs"]["N001"]["alerted"].get("ORDER_SOON") == "2026-10-09"
    assert "ORDER_SOON" in out1 and "telegram disabled" in out1      # first run: digest + alert to stdout
    # same day, second run: alert already sent today, not the first run -> nothing
    assert agent.run(args) == 0
    out2 = capsys.readouterr().out
    assert "nothing sent" in out2


def test_cli_dry_run_subprocess_no_secrets():
    env = {k: v for k, v in os.environ.items()
           if k not in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "TME_TOKEN", "TME_SECRET", "MOUSER_API_KEY")}
    r = subprocess.run([sys.executable, AGENT, "--dry-run", "--offline", "--today", "2026-10-09"],
                       capture_output=True, text=True, env=env, timeout=60)
    assert r.returncode == 0, r.stderr
    assert "# AR-Mini · parts report" in r.stdout and "N001" in r.stdout
