# -*- coding: utf-8 -*-
import json, os, base64, sys, glob, re, csv, io, html, datetime
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

BASE = os.path.dirname(os.path.abspath(__file__))
PASSWORD = sys.argv[1] if len(sys.argv) > 1 else "giulu2026"
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(BASE)

HUBNAME = {
 "F0BF261FL2V":"Boti/Vult/Licenciados","F0BF0AM9VFU":"Eudora",
 "F0BF22MAAGZ":"Bens de Consumo","F0BF426QKB6":"Novos Negócios","F0BEYAQ8Y4E":"GEO"}
HUBCOLOR = {"Boti/Vult/Licenciados":"#A66BFF","Eudora":"#F0529C","Bens de Consumo":"#3DA5FF","Novos Negócios":"#1FD6A6","GEO":"#FF8A3D"}

def clean_csv(text):
    m = re.search(r'<file_content_[0-9a-z]+>\s*(.*?)\s*</file_content_[0-9a-z]+>', text, re.S)
    if m: text = m.group(1)
    i = text.find('Tarefa')
    if i > 0: text = text[i:]
    return text.strip() + "\n"

raw_by_id = {}
for p in glob.glob(os.path.join(BASE, "csv", "*.csv")):
    fid = os.path.splitext(os.path.basename(p))[0]
    raw_by_id[fid] = clean_csv(open(p, encoding="utf-8").read())

DONE_RE = re.compile(r'(conclu|enviad|atend|aprov)')
def parse_tasks():
    out=[]
    for fid,body in raw_by_id.items():
        hub=HUBNAME.get(fid,fid)
        rows=list(csv.DictReader(io.StringIO(body)))
        for r in rows:
            tarefa=(r.get('Tarefa') or '').strip()
            if not tarefa: continue
            status=(r.get('Status') or '').strip()
            prazo=(r.get('Prazo') or '').strip()
            cb=(r.get('Concluída') or r.get('Concluida') or '').strip().lower()=='true'
            done = cb or bool(DONE_RE.search(status.lower()))
            draw=(r.get('Destinatário') or r.get('Destinatario') or '')
            dests=[seg.strip().split('@')[0].lower() for seg in re.split('[;,]',draw) if seg.strip()]
            desc=(r.get('Descrição') or r.get('Descricao') or '').strip()
            out.append({'hub':hub,'tarefa':tarefa,'status':status,'prazo':prazo,'done':done,'dests':dests,'desc':desc})
    return out
TASKS=parse_tasks()

# ---- classificação de esforço ----
CATS=[("Planejamento",3.0,"#F0529C",["planejamento","plano tát","plano tat","plan tá","plan ta","estratég","estrateg","tático","tatico","plano ","plan "]),
      ("Análise/Deck",2.5,"#3DA5FF",["apresenta","deck","estudo","análise","analise","pesquisa","cenário","cenario","score","insight","monitor"]),
      ("Mapeamento/Curadoria",2.0,"#FBD14E",["mapeamento","mapear","curadoria","mailing","big name","ugc","perfis","match"]),
      ("Briefing",1.0,"#22C978",["briefing"]),
      ("Outros",1.5,"#8f8b7c",[])]
def classify(t):
    s=(t['tarefa']+" "+t['desc']+" "+t['status']).lower()
    for name,w,col,kws in CATS:
        if kws and any(k in s for k in kws):
            return name,w,col
    return "Outros",1.5,"#8f8b7c"

def esf(tasks):
    d={c[0]:0 for c in CATS}; wsum=0.0
    for t in tasks:
        n,w,_=classify(t); d[n]+=1; wsum+=w
    return d,wsum

# ---- ORG ----
ORG=[
 {"lvl":"Diretoria","people":[{"n":"Giulia Sinhorini","u":"giu","t":"Diretora de Planejamento, BI e Social","hub":"Todas as marcas"}]},
 {"lvl":"Head","people":[{"n":"Luana","u":"luana","t":"Head de Planejamento","hub":"Todos os hubs"}]},
 {"lvl":"Gerência","people":[
   {"n":"Gustavo Pires","u":"gustavo","t":"Gerente de Planejamento","hub":"Beleza · Novos Negócios · GEO","hubs":["Boti/Vult/Licenciados","Novos Negócios","GEO"]},
   {"n":"Su Rosa","u":"suelyn","t":"Gerente de Planejamento","hub":"Bens de Consumo","hubs":["Bens de Consumo"]}]},
 {"lvl":"Supervisão","people":[
   {"n":"Giovana Marçon","u":"giovana","t":"Supervisora de Planejamento","hub":"Boticário · QDB · Vult · Licenciadas","hubs":["Boti/Vult/Licenciados"]},
   {"n":"Sarah Mendonça","u":"sarah","t":"Supervisora de Planejamento Criativo","hub":"Eudora","hubs":["Eudora"]}]},
 {"lvl":"Coordenação","people":[
   {"n":"Raissa Lemos Rocha","u":"raissa","t":"Coordenadora de Planejamento","hub":"Bens de Consumo","hubs":["Bens de Consumo"]}]},
 {"lvl":"Especialista","people":[
   {"n":"Matheus Gomes","u":"matheus.gomes","t":"Especialista de Planejamento","hub":"Boticário · QDB · Vult · Licenciadas","hubs":["Boti/Vult/Licenciados"]},
   {"n":"Cauã Sampaio","u":"caua","t":"Especialista de Planejamento","hub":"Bens de Consumo","hubs":["Bens de Consumo"]},
   {"n":"Gabô","u":"gabriela.barbosa","t":"Especialista em Planejamento & Influência II","hub":"Novos Negócios","hubs":["Novos Negócios"]},
   {"n":"Luiza Moraes","u":"luiza.moraes","t":"Especialista de Planejamento GEO","hub":"GEO · Samsung e Fiat","hubs":["GEO"]}]},
 {"lvl":"Analista","people":[
   {"n":"Olivia Villani","u":"olivia","t":"Analista de Planejamento","hub":"Eudora","hubs":["Eudora"]},
   {"n":"Alana Barros","u":"alana.barros","t":"Analista de Curadoria Jr.","hub":"Boticário · QDB · Vult · Licenciadas","hubs":["Boti/Vult/Licenciados"]},
   {"n":"Juliana Bandeira","u":"juliana","t":"Analista de Planejamento Jr.","hub":"Bens de Consumo","hubs":["Bens de Consumo"]},
   {"n":"Nicole Cantagallo","u":"nicole.cantagallo","t":"Analista de Planejamento","hub":"Novos Negócios","hubs":["Novos Negócios"]}]},
]
VAGAS=[
 {"role":"Supervisor(a) de Planejamento","hub":"Bens de Consumo","nivel":"Supervisão"},
 {"role":"Analista de Planejamento II e III","hub":"Boticário · QDB · Vult · Licenciadas","nivel":"Analista"},
 {"role":"Analista de Planejamento II","hub":"Bens de Consumo","nivel":"Analista"},
]

def today0():
    return datetime.date.today()
def dleft(prazo):
    try:
        y,m,d=map(int,prazo.split('-')); return (datetime.date(y,m,d)-today0()).days
    except: return None

def person_open(u):
    return [t for t in TASKS if (not t['done']) and (u in t['dests'])]

def esc(s): return html.escape(s or "")

# ---------------- ENCRYPTION / LOADER ----------------
def encrypt(inner, password):
    salt=os.urandom(16); iv=os.urandom(12)
    key=PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=salt,iterations=200000).derive(password.encode())
    ct=AESGCM(key).encrypt(iv, inner.encode('utf-8'), None)
    return base64.b64encode(salt+iv+ct).decode()

def loader(title, subtitle, blob):
    return LOADER_TPL.replace("__TITLE__",esc(title)).replace("__SUB__",esc(subtitle)).replace("__BLOB__",blob)

LOADER_TPL=r'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>__TITLE__ · Publination</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,400;0,500;0,600;0,700;0,800;1,700&display=swap" rel="stylesheet">
<style>:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;background:radial-gradient(900px 500px at 80% -10%,#1a1b17,#0f100e 60%),#0f100e;font-family:Poppins,system-ui,sans-serif;color:#FFF7CF}
.box{background:#1b1c19;border:1px solid rgba(255,247,207,.12);border-radius:20px;padding:34px 30px;width:360px;text-align:center}
.logo{font-weight:800;font-size:22px;letter-spacing:-.03em;margin-bottom:2px}.logo i{font-style:italic;font-weight:700}
.lock{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#D9094F;font-weight:600;margin-bottom:16px}
h1{font-size:17px;margin:0 0 4px;font-weight:600}p{color:#8f8b7c;font-size:12.5px;margin:0 0 18px}
input{width:100%;padding:12px 13px;border:1px solid rgba(255,247,207,.16);border-radius:12px;font-size:14px;margin-bottom:10px;background:#141513;color:#FFF7CF;font-family:inherit}
input:focus{outline:none;border-color:#D9094F}
button{width:100%;padding:12px;border:0;border-radius:12px;background:#D9094F;color:#fff;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit}
.err{color:#F5385D;font-size:12px;min-height:16px;margin-top:8px}</style></head>
<body><div class="box"><div class="logo">PUBLI<i>NATION</i></div><div class="lock">Área protegida</div>
<h1>__TITLE__</h1><p>__SUB__</p>
<input id="pw" type="password" placeholder="senha" autofocus onkeydown="if(event.key==='Enter')go()">
<button onclick="go()">Entrar</button><div class="err" id="err"></div></div>
<script>
const B64="__BLOB__";
async function go(){const pw=document.getElementById('pw').value;const err=document.getElementById('err');
if(!pw){err.textContent='Digite a senha.';return;}err.textContent='abrindo…';
try{const raw=Uint8Array.from(atob(B64),c=>c.charCodeAt(0));const salt=raw.slice(0,16),iv=raw.slice(16,28),data=raw.slice(28);
const km=await crypto.subtle.importKey('raw',new TextEncoder().encode(pw),'PBKDF2',false,['deriveKey']);
const key=await crypto.subtle.deriveKey({name:'PBKDF2',salt,iterations:200000,hash:'SHA-256'},km,{name:'AES-GCM',length:256},false,['decrypt']);
const pt=await crypto.subtle.decrypt({name:'AES-GCM',iv},key,data);
document.open();document.write(new TextDecoder().decode(pt));document.close();
}catch(e){err.textContent='Senha incorreta.';}}
</script></body></html>'''

print("build.py carregado — TASKS:", len(TASKS))

# ================= HTML SHARED =================
NAV_LINKS=[("index.html","Início"),("pautas.html","Pautas"),("organograma.html","Organograma"),("marcas.html","Marcas"),("publigif.html","PubliGIF"),("estimativas.html","Estimativas"),("mapeamento.html","Mapeamento"),("ugc.html","UGC")]
def nav(active):
    items="".join(f'<a href="{h}" class="{ "on" if h==active else "" }">{esc(l)}</a>' for h,l in NAV_LINKS)
    return f'<div class="nav"><a class="brand" href="index.html">PUBLI<i>NATION</i></a><span class="sp"></span>{items}</div>'

SHARED_CSS=r'''
:root{--bg:#0f100e;--card:#1b1c19;--card2:#212320;--line:rgba(255,247,207,.10);--line2:rgba(255,247,207,.16);--ink:#FFF7CF;--ink2:#c7c2ac;--ink3:#8f8b7c;--brand:#D9094F;--g1:#DB1150;--g2:#E9644F;--g3:#FBCB4E;--grad:linear-gradient(90deg,var(--g1),var(--g2),var(--g3));}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(1200px 600px at 80% -10%,#1a1b17,var(--bg) 55%) fixed,var(--bg);color:var(--ink);font-family:"Poppins",system-ui,sans-serif;-webkit-font-smoothing:antialiased;font-size:14px}
.nav{display:flex;align-items:center;gap:6px;padding:14px 22px;border-bottom:1px solid var(--line);flex-wrap:wrap;position:sticky;top:0;background:rgba(15,16,14,.85);backdrop-filter:blur(10px);z-index:10}
.nav .brand{font-weight:800;font-size:18px;letter-spacing:-.03em;color:var(--ink);text-decoration:none;margin-right:8px}
.nav .brand i{font-style:italic;font-weight:700}
.nav .sp{flex:1}
.nav a{color:var(--ink2);text-decoration:none;font-size:13px;font-weight:500;padding:7px 13px;border-radius:999px}
.nav a:hover{color:var(--ink);background:rgba(255,247,207,.06)}
.nav a.on{background:var(--brand);color:#fff}
.wrap{max-width:1240px;margin:0 auto;padding:28px 22px 80px}
.eyebrow{font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.16em;color:var(--brand)}
h1{font-size:27px;font-weight:700;letter-spacing:-.02em;margin:6px 0 3px}
.sub{color:var(--ink3);font-size:13px;margin-bottom:22px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:26px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 17px}
.kpi .n{font-size:30px;font-weight:800;letter-spacing:-.03em;line-height:1}
.kpi .l{font-size:10.5px;color:var(--ink3);margin-top:7px;text-transform:uppercase;letter-spacing:.05em;font-weight:600}
.lvl{margin:22px 0}
.lvltag{display:inline-block;font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:var(--ink3);border-left:2px solid var(--line2);padding-left:10px;margin-bottom:12px}
.row{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.pcard{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:15px 16px;display:flex;flex-direction:column;gap:10px}
.phead{display:flex;align-items:center;gap:11px}
.av{width:42px;height:42px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#141513;font-weight:700;font-size:15px;flex:0 0 auto}
.pn{font-weight:600;font-size:15px}
.pt{font-size:11px;color:var(--ink3);line-height:1.3}
.hchip{font-size:10px;padding:2px 8px;border-radius:6px;font-weight:600;display:inline-block}
.prow{display:flex;align-items:center;gap:8px;justify-content:space-between}
.cnt{font-size:12px;color:var(--ink2)}.cnt b{color:var(--ink);font-size:15px}
.nivchip{font-size:10px;font-weight:700;padding:3px 9px;border-radius:999px}
.esfbar{display:flex;height:7px;border-radius:5px;overflow:hidden;background:rgba(255,247,207,.08)}
.esfbar i{display:block;height:100%}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:11px;color:var(--ink3);margin:2px 0 20px}
.legend span{display:inline-flex;align-items:center;gap:5px}.legend b{width:9px;height:9px;border-radius:2px;display:inline-block}
.times{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:8px}
.tcard{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;border-top:3px solid var(--brand)}
.tname{font-weight:700;font-size:15px;margin-bottom:8px}
.tstat{display:flex;gap:14px;margin-bottom:10px;flex-wrap:wrap}
.tstat div{font-size:10.5px;color:var(--ink3)}.tstat b{display:block;font-size:18px;color:var(--ink);font-weight:800;white-space:nowrap}
.member{display:flex;flex-direction:column;padding:7px 0;border-bottom:1px solid var(--line)}.member:last-child{border-bottom:0}.mn{font-size:13px;font-weight:600}.mt{font-size:11px;color:var(--ink3)}.mcount{font-size:11px;color:var(--ink3);margin-bottom:10px}
.lockbtn{display:inline-flex;align-items:center;gap:8px;background:var(--card);border:1px solid var(--line2);color:var(--ink);text-decoration:none;padding:12px 18px;border-radius:14px;font-weight:600;font-size:13px}
.lockbtn:hover{border-color:var(--brand)}
.gradbar{height:4px;background:var(--grad);border-radius:3px;margin:0 0 22px}
'''

def initials(nm):
    p=[x for x in nm.split() if x]; return ((p[0][0] if p else "?")+(p[1][0] if len(p)>1 else "")).upper()
LVLCOLOR={"Diretoria":"#D9094F","Head":"#E9644F","Gerência":"#A66BFF","Supervisão":"#F0529C","Coordenação":"#3DA5FF","Especialista":"#FBD14E","Analista":"#22C978"}
def nivchip(avg):
    if avg>=2.3: return ("Pesado","#F5385D","rgba(245,56,93,.15)")
    if avg>=1.8: return ("Médio","#FBD14E","rgba(251,209,78,.15)")
    if avg>0: return ("Leve","#22C978","rgba(34,201,120,.15)")
    return ("—","#8f8b7c","rgba(255,247,207,.06)")
def esfbar(mix):
    tot=sum(mix.values()) or 1; segs=""
    for name,w,col,_ in CATS:
        n=mix.get(name,0)
        if n: segs+=f'<i style="width:{n/tot*100:.1f}%;background:{col}" title="{name}: {n}"></i>'
    return f'<div class="esfbar">{segs}</div>'
def esf_legend():
    return '<div class="legend">'+''.join(f'<span><b style="background:{c}"></b>{esc(n)}</span>' for n,w,c,_ in CATS)+'</div>'

def person_card(p):
    hub=p.get('hubs',[None])[0] if p.get('hubs') else None
    hcol=HUBCOLOR.get(hub,"#8f8b7c")
    avc=LVLCOLOR.get(p['_lvl'],"#D9094F")
    return (f'<div class="pcard"><div class="phead"><div class="av" style="background:{avc}">{esc(initials(p["n"]))}</div>'
            f'<div><div class="pn">{esc(p["n"])}</div><div class="pt">{esc(p["t"])}</div></div></div>'
            f'<div><span class="hchip" style="background:{hcol}22;color:{hcol}">{esc(p["hub"])}</span></div></div>')

def build_organograma():
    total_people=sum(len(l["people"]) for l in ORG)
    lvls_html=""
    for l in ORG:
        for p in l["people"]: p["_lvl"]=l["lvl"]
        cards="".join(person_card(p) for p in l["people"])
        lvls_html+=f'<div class="lvl"><div class="lvltag">{esc(l["lvl"])}</div><div class="row">{cards}</div></div>'
    ORGHUBS=[("Beleza","#A66BFF","Boticário · QDB · Vult · Licenciadas · Eudora"),
             ("Bens de Consumo","#3DA5FF",""),
             ("Novos Negócios","#1FD6A6",""),
             ("GEO","#FF8A3D","Samsung · Fiat")]
    PAUTA2HUB={"Boti/Vult/Licenciados":"Beleza","Eudora":"Beleza","Bens de Consumo":"Bens de Consumo","Novos Negócios":"Novos Negócios","GEO":"GEO"}
    def orghubs_of(p): return {PAUTA2HUB.get(h,h) for h in p.get("hubs",[])}
    times=""
    for name,col,subt in ORGHUBS:
        ppl=[p for l in ORG for p in l["people"] if name in orghubs_of(p)]
        lis="".join(f'<div class="member"><span class="mn">{esc(p["n"])}</span><span class="mt">{esc(p["t"])}</span></div>' for p in ppl) or '<div class="member"><span class="mt">\u2014</span></div>'
        sub=f'{len(ppl)} pessoa(s)'+(f' · {subt}' if subt else '')
        times+=(f'<div class="tcard" style="border-top-color:{col}"><div class="tname">{esc(name)}</div>'
                f'<div class="mcount">{esc(sub)}</div>{lis}</div>')
    body=f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Organograma \u00b7 Planejamento Publination</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,400;0,500;0,600;0,700;0,800;1,700&display=swap" rel="stylesheet">
<style>{SHARED_CSS}</style></head><body>{nav("organograma.html")}
<div class="wrap">
<div class="eyebrow">Planejamento Publination</div><h1>Organograma do time</h1>
<div class="sub">Quem trabalha com o qu\u00ea \u00b7 estrutura do time de planejamento</div>
<div class="kpis">
<div class="kpi"><div class="n">{total_people}</div><div class="l">Pessoas no time</div></div>
<div class="kpi"><div class="n">4</div><div class="l">Hubs</div></div>
<div class="kpi"><div class="n">7</div><div class="l">N\u00edveis</div></div>
</div>
{lvls_html}
<div class="lvl"><div class="lvltag">Quem trabalha com o qu\u00ea</div><div class="times">{times}</div></div>
<div style="margin-top:26px"><a class="lockbtn" href="pautas.html">\U0001F512 Gest\u00e3o &amp; Vagas est\u00e1 no Painel de Pautas (restrito)</a></div>
</div></body></html>'''
    open(os.path.join(OUTDIR,"organograma.html"),"w",encoding="utf-8").write(body)
    return total_people,0

def build_gestao():
    vagas="".join(f'<div class="pcard"><div class="prow"><div><div class="pn">{esc(v["role"])}</div><div class="pt">{esc(v["hub"])}</div></div>'
                  f'<span class="hchip" style="background:rgba(217,9,79,.15);color:#F5385D">{esc(v["nivel"])}</span></div></div>' for v in VAGAS)
    lead=""
    for l in ORG[:2]:
        for p in l["people"]:
            p["_lvl"]=l["lvl"]; lead+=person_card(p)
    for l in ORG:
        for p in l["people"]: p["_lvl"]=l["lvl"]
    inner=f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gestão &amp; Vagas · Publination</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,400;0,500;0,600;0,700;0,800;1,700&display=swap" rel="stylesheet">
<style>{SHARED_CSS}
table{{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden}}
th,td{{padding:10px 14px;font-size:13px;text-align:left;border-bottom:1px solid var(--line)}}
th{{font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink3);font-weight:600}}
tr:last-child td{{border-bottom:0}}</style></head><body>{nav("organograma.html")}
<div class="wrap">
<div class="eyebrow">Área da liderança · Giu &amp; Lu</div><h1>Gestão &amp; Vagas</h1>
<div class="sub">Visão restrita de headcount e planejamento de time</div>
<div class="gradbar"></div>
<div class="lvl"><div class="lvltag">Vagas abertas — {len(VAGAS)}</div><div class="row">{vagas}</div></div>
<div class="lvl"><div class="lvltag">Liderança</div><div class="row">{lead}</div></div>
</div></body></html>'''
    blob=encrypt(inner,PASSWORD)
    open(os.path.join(OUTDIR,"gestao.html"),"w",encoding="utf-8").write(loader("Gestão & Vagas","Conteúdo restrito à liderança. Digite a senha.",blob))


def gestao_html():
    vg="".join(
      f'<div style="background:var(--card);border:1px solid var(--line);border-left:3px solid var(--brand);border-radius:14px;padding:14px 16px;display:flex;justify-content:space-between;align-items:center;gap:12px">'
      f'<div><div style="font-weight:600;font-size:14px;color:var(--ink)">{esc(v["role"])}</div>'
      f'<div style="font-size:11.5px;color:var(--ink3);margin-top:2px">{esc(v["hub"])}</div></div>'
      f'<span style="font-size:11px;font-weight:600;color:#F5385D;background:rgba(245,56,93,.15);padding:4px 10px;border-radius:999px;white-space:nowrap">{esc(v["nivel"])}</span></div>'
      for v in VAGAS)
    lead=""
    for l in ORG[:2]:
        for p in l["people"]:
            ini=initials(p["n"]); col=LVLCOLOR.get(l["lvl"],"#D9094F")
            lead+=(f'<div style="background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;display:flex;align-items:center;gap:12px">'
                   f'<div style="width:40px;height:40px;border-radius:50%;background:{col};display:flex;align-items:center;justify-content:center;color:#141513;font-weight:700;font-size:14px">{esc(ini)}</div>'
                   f'<div><div style="font-weight:600;font-size:14px">{esc(p["n"])}</div><div style="font-size:11.5px;color:var(--ink3)">{esc(p["t"])}</div></div></div>')
    return (
      '<div style="padding:6px 0 30px">'
      '<div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:var(--ink3);border-left:2px solid rgba(255,247,207,.16);padding-left:10px;margin:6px 0 12px">'
      f'Vagas abertas \u2014 {len(VAGAS)}</div>'
      f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;margin-bottom:26px">{vg}</div>'
      '<div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:var(--ink3);border-left:2px solid rgba(255,247,207,.16);padding-left:10px;margin:6px 0 12px">Lideran\u00e7a</div>'
      f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px">{lead}</div>'
      '<div style="font-size:11.5px;color:var(--ink3);margin-top:18px">\u00c1rea restrita \u00b7 Giu &amp; Lu</div>'
      '</div>')

def build_pautas():
    tpl=open(os.path.join(BASE,"dashboard_template.html"),encoding="utf-8").read()
    stub=("<script>\nwindow.__RAW_BY_ID="+json.dumps(raw_by_id,ensure_ascii=False)+
        ";\nwindow.__GESTAO_HTML="+json.dumps(gestao_html(),ensure_ascii=False)+
        ";\nwindow.cowork={callMcpTool:async function(t,a){return {content:[{text:\"<file_content_aa>\\n\"+(window.__RAW_BY_ID[a.file_id]||\"\")+\"\\n</file_content_aa>\"}]};}};\n</script>\n")
    inner=tpl.replace("<body>","<body>\n"+stub,1)
    inner=inner.replace("botão <b>Recarregar</b> no topo puxa de novo","atualizado automaticamente às 11h")
    blob=encrypt(inner,PASSWORD)
    open(os.path.join(OUTDIR,"pautas.html"),"w",encoding="utf-8").write(loader("Painel de Pautas","Acesso restrito à liderança. Digite a senha.",blob))

build_pautas()
tp,oa=build_organograma()
print(f"OK -> pautas.html + organograma.html ({tp} pessoas, {oa} abertas) + gestao.html em {OUTDIR}")
