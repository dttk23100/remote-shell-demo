const OWNER = process.env.GIST_OWNER || "dttk23100";
const GIST_ID = process.env.GIST_ID;

async function raw(file) {
  const url = `https://gist.githubusercontent.com/${OWNER}/${GIST_ID}/raw/${file}?t=${Date.now()}`;
  const r = await fetch(url, { cache: "no-store", headers: { "User-Agent": "remote-shell-demo" } });
  if (!r.ok) throw new Error(`${file}: HTTP ${r.status}`);
  return r.text();
}

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store, max-age=0");
  if (!GIST_ID) return res.status(500).json({ error: "GIST_ID is not set" });
  try {
    const [commandRaw, output, statusRaw] = await Promise.all([
      raw("command.json"),
      raw("output.txt"),
      raw("status.json"),
    ]);
    let command = {};
    let status = {};
    try { command = JSON.parse(commandRaw); } catch (_) {}
    try { status = JSON.parse(statusRaw); } catch (_) {}
    res.status(200).json({ command, output, status });
  } catch (e) {
    res.status(502).json({ error: String(e.message || e) });
  }
};
