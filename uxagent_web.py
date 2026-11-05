"""Interface web local de baixa fidelidade para T1/T2."""
from __future__ import annotations

import json
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from mechanisms import MechanismConfig
from uxagent_session import UXAgentSession

HTML = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>UXAgent — Lobby cooperativo</title>
<style>
:root{font-family:Inter,Segoe UI,sans-serif;color:#172033;background:#eef2f8;line-height:1.5;--ink:#172033;--muted:#66738d;--line:#dce3ef;--brand:#3457d5;--brand-dark:#263fa9}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 85% -10%,#dfe7ff 0,transparent 34%),#eef2f8}.shell{max-width:1280px;margin:auto;padding:32px 24px 48px}
header{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;margin-bottom:26px}header>div:first-child{min-width:0}
h1,h2,h3{margin:0 0 8px}h1{font-size:32px;letter-spacing:-.03em}h2{font-size:18px;letter-spacing:-.01em}.muted{color:var(--muted);font-size:14px}
.grid{display:grid;grid-template-columns:1.35fr 1fr 1fr;gap:18px}.card{background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:18px;padding:20px;box-shadow:0 10px 28px #25365b12}.card>h2{display:flex;align-items:center;gap:8px}.card>h2:before{content:"";width:4px;height:18px;border-radius:4px;background:#8ba3ff}
.wide{grid-column:span 2}.members{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.member{border:1px solid var(--line);border-radius:13px;padding:14px;background:#fbfcff;transition:transform .15s,box-shadow .15s}.member:hover{transform:translateY(-2px);box-shadow:0 6px 16px #25365b12}.member strong{display:block;margin-bottom:2px}.tag{display:inline-block;background:#edf1fa;border-radius:999px;padding:3px 8px;font-size:12px;margin:5px 3px 0 0}
button,select{font:inherit;border:1px solid #bbc5d8;border-radius:10px;padding:9px 12px;background:#fff;color:inherit}button{cursor:pointer;transition:background .15s,border-color .15s,transform .15s}button:hover:not(:disabled){border-color:#8194cf;background:#f7f9ff;transform:translateY(-1px)}button.primary{background:var(--brand);color:#fff;border-color:var(--brand);box-shadow:0 5px 12px #3457d540}button.primary:hover:not(:disabled){background:var(--brand-dark);border-color:var(--brand-dark)}button:disabled{opacity:.5;cursor:not-allowed}button:focus-visible,select:focus-visible{outline:3px solid #9db4ff;outline-offset:2px}
.actions{display:flex;flex-wrap:wrap;gap:9px}.assignment{display:grid;grid-template-columns:1fr 1fr auto;gap:8px;margin:14px 0 0}.row{display:flex;align-items:center;justify-content:space-between;gap:8px;border-bottom:1px solid #edf0f6;padding:10px 0}.row:last-child{border-bottom:0}
.feedback{margin-top:14px;padding:12px 14px;border-radius:11px;background:#f1f4fb;color:#43516e}.success{background:#e8f7ed;color:#176b3a}.error{background:#fff0f0;color:#9a3030}.status{display:inline-block;border-radius:999px;padding:4px 10px;background:#edf1fa;font-size:13px}.status.active{color:#2946ae}.status.completed{color:#176b3a;background:#e8f7ed}
ol{padding-left:24px;margin:8px 0}.empty{color:#7b8498;font-style:italic}.pill{font-weight:600;color:#3457d5}
@media(max-width:900px){.grid{grid-template-columns:1fr}.wide{grid-column:auto}.members{grid-template-columns:1fr 1fr}.assignment{grid-template-columns:1fr 1fr}.assignment button{grid-column:span 2}header{flex-direction:column}header button{width:100%}}
@media(max-width:560px){.shell{padding:22px 14px 36px}h1{font-size:27px}.card{padding:16px;border-radius:15px}.members{grid-template-columns:1fr}.actions button{width:100%}}
@media(max-width:900px){.grid{grid-template-columns:1fr}.wide{grid-column:auto}.members{grid-template-columns:1fr}header{flex-direction:column}header button{width:100%}}
</style></head>
<body><main class="shell"><header><div><h1>Lobby cooperativo</h1><div class="muted">UXAgent · <span id="task"></span> · contrato <span id="version"></span></div></div><div><button id="feed" hidden>Simular atualização do feed</button></div></header>
<section class="grid"><article class="card wide"><h2>Objetivo</h2><p id="objective"></p><div id="feedback" class="feedback" aria-live="polite">Carregando...</div></article>
<article class="card"><h2>Estado</h2><div class="row"><span>Etapa</span><strong id="step"></strong></div><div class="row"><span>Revisado</span><strong id="reviewed"></strong></div><div class="row"><span>Status</span><strong id="status" class="status"></strong></div></article>
<article class="card wide"><h2>Integrantes e funções</h2><div id="members" class="members"></div><div class="assignment"><select id="member"></select><select id="role"></select><button id="assign" class="primary">Atribuir</button></div></article>
<article class="card"><h2>Feed</h2><p id="feedText" class="muted"></p><div id="completedSteps"></div><button id="refresh" hidden>Atualizar observação</button></article>
<article class="card"><h2>Ordem das etapas</h2><ol id="order"></ol><button id="defaultOrder">Usar ordem padrão</button></article>
<article class="card"><h2>Suporte</h2><div class="actions"><button id="checklist">Abrir checklist</button><button id="help">Abrir ajuda</button></div><p id="support" class="muted"></p></article>
<article class="card wide"><h2>Ações da tarefa</h2><div id="actions" class="actions"></div><button id="evaluate" class="primary" hidden>Avaliar tarefa</button></article>
<article class="card wide"><h2>Histórico observável</h2><ol id="history"></ol></article></section></main>
<script>
let state;
const $=id=>document.getElementById(id);
const actionLabels={remove_assignment:'Remover atribuição indisponível',open_checklist:'Abrir checklist',refresh_feed:'Atualizar observação',send_ping:'Comunicar próxima etapa',review_plan:'Revisar plano',confirm_plan:'Confirmar plano'};
async function request(url, options={}){const r=await fetch(url,options);const data=await r.json();if(!r.ok)throw Error(data.error||'Falha de comunicação');return data}
function action(name,arguments_={}){return request('/api/action',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({name,arguments:arguments_})}).then(render).catch(showError)}
function showError(error){$('feedback').textContent=error.message;$('feedback').className='feedback error'}
function render(s){state=s;$('task').textContent=s.task_id;$('version').textContent=s.ui_version;$('objective').textContent=s.objective;$('step').textContent=s.step;$('reviewed').textContent=s.reviewed?'sim':'não';$('status').textContent=s.status;$('status').className='status '+s.status;$('feedback').textContent=s.feedback||'Sem feedback';$('feedback').className='feedback '+(s.status==='completed'?'success':'');
 $('feedText').textContent=s.feed.message+' (revisão '+s.feed.revision+')';$('completedSteps').textContent=s.feed.completed_steps.join(' → ')||'Nenhuma etapa concluída no feed';$('feed').hidden=!['T2','T3','T4'].includes(s.task_id)||s.feed.revision>0;$('refresh').hidden=!['T2','T3','T4'].includes(s.task_id);
 $('members').innerHTML=Object.entries(s.members).map(([m,v])=>'<div class="member"><strong>'+m+'</strong><span class="muted">'+(s.assignments[m]||'Sem função')+'</span><div>'+v.capabilities.map(x=>'<span class="tag">'+x+'</span>').join('')+'</div></div>').join('');
 $('member').innerHTML=Object.keys(s.members).map(m=>'<option>'+m+'</option>').join('');$('role').innerHTML=s.required_roles.map(r=>'<option>'+r+'</option>').join('');
 $('order').innerHTML=s.step_order.map(x=>'<li>'+x+'</li>').join('');$('support').textContent=s.checklist_open?'Checklist aberto.':(s.help_topic?'Ajuda: '+s.help_topic:'');
 $('actions').innerHTML=s.available_actions.filter(x=>!['select_role','set_step_order'].includes(x.name)).map(x=>'<button data-action="'+x.name+'" aria-label="'+(actionLabels[x.name]||x.name)+'">'+(actionLabels[x.name]||x.name)+'</button>').join('');$('evaluate').hidden=s.status!=='completed';
 $('actions').querySelectorAll('button').forEach(b=>b.onclick=()=>{if(b.dataset.action==='open_help')action('open_help',{topic:'task_dependencies'});else if(b.dataset.action==='remove_assignment')action('remove_assignment',{member:'member_C'});else action(b.dataset.action)});
 $('history').innerHTML=s.history.length?s.history.map(x=>'<li><span class="pill">'+x.step+'</span> '+x.event+' — '+x.reason+'</li>').join(''):'<li class="empty">Nenhuma ação ainda.</li>';
}
async function load(){try{render(await request('/api/state'))}catch(e){showError(e)}}
$('assign').onclick=()=>action('select_role',{member:$('member').value,role:$('role').value});$('checklist').onclick=()=>action('open_checklist');$('help').onclick=()=>action('open_help',{topic:'task_dependencies'});$('refresh').onclick=()=>action('refresh_feed');$('feed').onclick=()=>request('/api/feed-update',{method:'POST'}).then(render).catch(showError);$('defaultOrder').onclick=()=>action('set_step_order',{steps:['LOCATE_RESOURCE','ACTIVATE_CHECKPOINT','TRANSPORT_RESOURCE']});load();
$('evaluate').onclick=()=>request('/api/evaluate',{method:'POST'}).then(result=>{$('feedback').textContent=result.reason;$('feedback').className='feedback '+(result.success?'success':'error')}).catch(showError);
</script></body></html>"""


class _Handler(BaseHTTPRequestHandler):
    server_version = "UXAgentWeb/1.0"

    def _json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/api/state":
            self._json(200, self.server.session.view_model())
            return
        if urlparse(self.path).path in {"/", "/index.html"}:
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._json(404, {"error": "Rota não encontrada."})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/action":
                result = self.server.session.dispatch(payload)
                self._json(200, self.server.session.view_model())
            elif self.path == "/api/feed-update":
                self.server.session.trigger_feed_update()
                self._json(200, self.server.session.view_model())
            elif self.path == "/api/evaluate":
                self._json(200, self.server.session.evaluate())
            else:
                self._json(404, {"error": "Rota não encontrada."})
        except (ValueError, TypeError, RuntimeError) as exc:
            self._json(400, {"error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        return


class UXAgentWebServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], session: UXAgentSession) -> None:
        super().__init__(address, _Handler)
        self.session = session


def create_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    task_id: str = "T1",
    log_dir: Path | None = None,
) -> UXAgentWebServer:
    session_id = f"web-{task_id.lower()}"
    log_path = log_dir / f"{session_id}.jsonl" if log_dir else None
    return UXAgentWebServer(
        (host, port),
        UXAgentSession(task_id, session_id=session_id, log_path=log_path),
    )


def serve(host: str = "127.0.0.1", port: int = 8765, task_id: str = "T1", log_dir: Path | None = Path("logs")) -> None:
    server = create_server(host, port, task_id, log_dir)
    try:
        print(f"UXAgent web: http://{host}:{port} ({task_id})")
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Interface web local do UXAgent")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--task", choices=("T1", "T2", "T3", "T4"), default="T1")
    args = parser.parse_args()
    serve(args.host, args.port, args.task)
