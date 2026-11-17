# Remote Shell — public demo

A public terminal dashboard that sends allowlisted commands to a consenting
macOS test host. The command bus is a GitHub Gist; the UI/API are on Vercel.

- Dashboard: `https://remote-shell-demo.vercel.app`
- Agent: `agent.py`
- Commands: read-only allowlist (whoami, hostname, pwd, date, uptime, uname,
  sw_vers, df, ls, ps, echo, say)
- No writes, no sudo, no network commands.

This is a demo of remote command execution, not a production C2.
