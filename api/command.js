const GIST_ID = process.env.GIST_ID;
const TOKEN = process.env.GH_TOKEN;

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store, max-age=0");
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "POST only" });
  }
  if (!GIST_ID || !TOKEN) return res.status(500).json({ error: "GIST_ID/GH_TOKEN not set" });

  let body = req.body;
  if (typeof body === "string") {
    try { body = JSON.parse(body); } catch (_) { body = {}; }
  }
  const cmd = String((body && body.cmd) || "").trim().slice(0, 2000);
  if (!cmd) return res.status(400).json({ error: "empty command" });

  const id = Date.now();
  const payload = {
    files: {
      "command.json": {
        content: JSON.stringify({ id, cmd, ts: id }),
      },
    },
  };

  try {
    const r = await fetch(`https://api.github.com/gists/${GIST_ID}`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${TOKEN}`,
        Accept: "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "remote-shell-demo",
      },
      body: JSON.stringify(payload),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      return res.status(502).json({ error: data.message || `GitHub HTTP ${r.status}` });
    }
    res.status(200).json({ ok: true, id });
  } catch (e) {
    res.status(502).json({ error: String(e.message || e) });
  }
};
