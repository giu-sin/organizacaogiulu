import json, os, base64, sys, glob
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

BASE = os.path.dirname(os.path.abspath(__file__))
password = sys.argv[1] if len(sys.argv) > 1 else "giulu2026"
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, "index.html")

raw_by_id = {}
for p in glob.glob(os.path.join(BASE, "csv", "*.csv")):
    fid = os.path.splitext(os.path.basename(p))[0]
    raw_by_id[fid] = open(p, encoding="utf-8").read()

tpl = open(os.path.join(BASE, "dashboard_template.html"), encoding="utf-8").read()
stub = ("<script>\nwindow.__RAW_BY_ID=" + json.dumps(raw_by_id, ensure_ascii=False) +
        ";\nwindow.cowork={callMcpTool:async function(t,a){return {content:[{text:\"<file_content_x>\\n\"+(window.__RAW_BY_ID[a.file_id]||\"\")+\"\\n</file_content_x>\"}]};}};\n</script>\n")
inner = tpl.replace("<body>", "<body>\n" + stub, 1)
inner = inner.replace("botão <b>Recarregar</b> no topo puxa de novo", "atualizado automaticamente às 11h")

salt = os.urandom(16); iv = os.urandom(12)
key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=200000).derive(password.encode())
ct = AESGCM(key).encrypt(iv, inner.encode("utf-8"), None)
blob = base64.b64encode(salt + iv + ct).decode()

loader = open(os.path.join(BASE, "loader_template.html"), encoding="utf-8").read().replace("__BLOB__", blob)
open(out, "w", encoding="utf-8").write(loader)
print("OK ->", out, "|", round(len(loader)/1024), "KB |", len(raw_by_id), "pautas")
