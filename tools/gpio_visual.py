"""Local visual viewer for TESTE PORTAS logs; never opens serial or changes mapping."""
import argparse
import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PINS = (0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33, 34, 35, 36, 39)
PATTERN = re.compile(r'^(\d+(?:\.\d+)?) (ESTADO|EVENTO) GPIO(\d+) (FECHADO|ABERTO|LOW|HIGH)(?: /| \[)')

def parse_log(text):
    states, events = {}, []
    for line in text.splitlines():
        if 'GUITAR LAB - TESTE PORTAS v1' in line:
            states, events = {}, []
        match = PATTERN.match(line)
        if not match:
            continue
        timestamp, kind, pin, level = match.groups()
        pin = int(pin)
        if pin not in PINS:
            continue
        down = level in ('FECHADO', 'LOW')
        row = dict(pin=pin, down=down, time=float(timestamp), initial=kind == 'ESTADO')
        states[pin] = row
        if kind == 'EVENTO':
            events.append(row)
    return dict(states=states, events=events[-30:])

PAGE = '''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Guitar Lab · Teste de portas</title><style>
*{box-sizing:border-box}body{margin:0;background:#10151e;color:#eff4fc;font:17px system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:30px 24px}h1{font-size:30px;margin:6px 0}p{color:#adbacc;line-height:1.5}#status{font-size:14px}#last{background:#202b3c;border-left:5px solid #69adff;padding:20px;border-radius:10px;margin:24px 0;font-size:26px;font-weight:700}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:12px}.pin{border:2px solid #354055;background:#1b2432;border-radius:12px;padding:17px;min-height:115px}.pin strong{display:block;font-size:25px}.pin span{display:block;margin-top:8px;font-size:14px;color:#b9c4d3}.pin.on{background:#164b37;border-color:#4ce0a0}.pin.on span{color:#bcffdf}.pin.initial{background:#463b20;border-color:#cda251}.pin.initial span{color:#ffe2a6}.pin.flash{box-shadow:0 0 0 3px #b8eaff}.muted{opacity:.5}section{margin-top:25px}h2{font-size:19px}li{padding:6px 0;color:#bbc7d8}.legend{font-size:14px}#error{color:#ffbbad}</style>
<main><div id="status">Conectando ao painel…</div><h1>Qual porta eu apertei?</h1><p>Aperte e solte um botão. O GPIO correspondente fica verde enquanto o contato está fechado.<br>Não há atribuição de cores nem alteração da pinagem.</p><div id="last" role="status" aria-live="polite">Aguardando o primeiro aperto…</div><div class="grid" id="grid"></div><p class="legend">Verde: contato fechado após mudança • Âmbar: já estava fechado na leitura inicial • Cinza: solto.<br>34/35/36/39: leitura bruta, sem pullup interno. Use resistor de 10 kΩ entre GPIO e 3V3; sem ele pode haver oscilações falsas.</p><div id="error"></div><section><h2>Últimas mudanças</h2><ol id="events"></ol></section></main><script>
const pins=PINS_JSON;const cards={};for(const p of pins){const c=document.createElement('div');c.className='pin';c.innerHTML='<strong>GPIO '+p+'</strong><span>Aguardando leitura</span>';grid.appendChild(c);cards[p]=c;}
let busy=false;async function update(){if(busy)return;busy=true;try{const r=await fetch('/state',{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();document.getElementById('status').textContent=d.reader_alive?'● Leitor do diagnóstico ativo':'○ Leitor encerrado — valores abaixo são históricos';document.getElementById('error').textContent='';for(const p of pins){const s=d.states[p],c=cards[p];c.className='pin'+(!d.reader_alive?' muted':'');if(!s){c.querySelector('span').textContent='Sem leitura';continue}if(s.down)c.classList.add(s.initial?'initial':'on');if(!s.initial&&Date.now()/1000-s.time<1)c.classList.add('flash');c.querySelector('span').textContent=p>=34?(s.down?'LOW':'HIGH')+' · sem pullup interno':(s.down?(s.initial?'Fechado desde o início':'FECHADO / APERTADO'):'ABERTO / SOLTO');}
const presses=d.events.filter(x=>x.down);const last=presses.at(-1);document.getElementById('last').textContent=last?'Última porta acionada: GPIO '+last.pin+(last.pin>=34?' — conferir pullup externo':''):'Aguardando o primeiro aperto…';const list=document.getElementById('events');list.replaceChildren();for(const e of d.events.slice(-12).reverse()){const li=document.createElement('li');li.textContent=new Date(e.time*1000).toLocaleTimeString('pt-BR')+' — GPIO '+e.pin+' — '+(e.pin>=34?(e.down?'LOW (sem pullup interno)':'HIGH (sem pullup interno)'):(e.down?'FECHOU / APERTOU':'ABRIU / SOLTOU'));list.appendChild(li);}}
catch(e){document.getElementById('status').textContent='Painel sem conexão';document.getElementById('error').textContent='Não foi possível atualizar. Os estados exibidos podem estar desatualizados.';for(const c of Object.values(cards))c.classList.add('muted');}finally{busy=false}}update();setInterval(update,250);
</script></html>'''.replace('PINS_JSON', json.dumps(PINS))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', required=True, type=Path)
    parser.add_argument('--reader-pid', required=True, type=int)
    parser.add_argument('--port', type=int, default=8767)
    args = parser.parse_args()
    def reader_alive():
        try:
            cmd = Path(f'/proc/{args.reader_pid}/cmdline').read_bytes()
            return b'guitar-live-ports.py' in cmd
        except OSError:
            return False
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                body, mime = PAGE.encode(), 'text/html; charset=utf-8'
            elif self.path == '/state':
                try:
                    content = args.log.read_text(encoding='utf8')
                except OSError:
                    content = ''
                data = parse_log(content)
                data['reader_alive'] = reader_alive()
                body, mime = json.dumps(data).encode(), 'application/json'
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *args):
            pass
    print(f'Painel: http://127.0.0.1:{args.port}', flush=True)
    HTTPServer(('127.0.0.1', args.port), Handler).serve_forever()

if __name__ == '__main__':
    main()
