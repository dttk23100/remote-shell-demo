const OWNER = process.env.GIST_OWNER || "dttk23100";
const GIST_ID = process.env.GIST_ID;

const TOKEN = process.env.GH_TOKEN;

async function gistFiles() {
  const r = await fetch(`https://api.github.com/gists/${GIST_ID}?t=${Date.now()}`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      Accept: "application/vnd.github+json",
      "User-Agent": "remote-shell-demo",
    },
  });
  if (!r.ok) throw new Error(`gist: HTTP ${r.status}`);
  const data = await r.json();
  return data.files || {};
}

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store, max-age=0");
  if (!GIST_ID) return res.status(500).json({ error: "GIST_ID is not set" });
  try {
    const files = await gistFiles();
    const commandRaw = files["command.json"]?.content || "{}";
    const output = files["output.txt"]?.content || "";
    const statusRaw = files["status.json"]?.content || "{}";
    let command = {};
    let status = {};
    try { command = JSON.parse(commandRaw); } catch (_) {}
    try { status = JSON.parse(statusRaw); } catch (_) {}
    res.status(200).json({ command, output, status });
  } catch (e) {
    res.status(502).json({ error: String(e.message || e) });
  }
};
