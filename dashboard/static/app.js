const $=id=>document.getElementById(id);
let last=null, fetching=false, historyKey='';
const stages=[['serial','USB e serial no Zorin','Placa identificada e comunicação estável.'],['button','Um botão físico','Apertos e solturas conferidos no monitor, sem eventos extras.'],['nine','Nove comandos em bancada','Cinco frets, duas palhetas, Start e Select testados.'],['whammy','Whammy analógico','Repouso estável e curso completo conferidos.'],['linux','Clone Hero no desktop','Controle virtual reconhecido e comandos mapeados.'],['ally','ROG Ally / SteamOS','Teste após reconexão e reinício no modo usado na viagem.'],['assembly','Impressão e montagem','Encaixes, movimento, isolamento e cabo revisados.'],['music','Pronto para a viagem','Música inteira e 30 minutos no Ally sem falhas.']];
for(const [key,title,desc] of stages){const label=document.createElement('label');label.className='check';const input=document.createElement('input');input.type='checkbox';input.id='check-'+key;input.onchange=async()=>{try{await post('/api/check',{key,value:input.checked});toast('Etapa salva neste computador.')}catch(e){input.checked=!input.checked;toast('Não foi possível salvar.')}};const text=document.createElement('span'),strong=document.createElement('strong'),small=document.createElement('small');strong.textContent=title;small.textContent=desc;text.append(strong,small);label.append(input,text);$('checks').append(label)}

const fretColors={green:'#5cdb63',red:'#ff6565',yellow:'#f5d24c',blue:'#63a7ff',orange:'#ffa34c'};
for(const [key,color] of Object.entries(fretColors)){
 const card=document.createElement('div');card.className='fret-test';card.style.setProperty('--fret-color',color);
 const title=document.createElement('strong');title.id='fret-title-'+key;
 const light=document.createElement('div');light.id='fret-light-'+key;light.className='fret-light';light.textContent='?';
 const count=document.createElement('small');count.id='fret-count-'+key;
 card.append(title,light,count);$('frets').append(card);
}
function renderFrets(s){for(const key of Object.keys(fretColors)){
 const f=s?.frets?.[key],known=s?.connected&&!s?.bridge?.timed_out&&f?.pressed!==null&&f?.pressed!==undefined;
 $('fret-title-'+key).textContent=f?f.name+' · D'+f.pin:key;
 $('fret-light-'+key).className='fret-light'+(known&&f.pressed?' pressed':'');
 $('fret-light-'+key).textContent=known?(f.pressed?'Apertado':'Solto'):'Sem leitura';
 $('fret-count-'+key).textContent=f?f.presses+' apertos · '+f.releases+' solturas':'Aguardando';
}}


for(const pin of [17,16,18,21,15]){
 const el=document.createElement('div');el.id='scan-pin-'+pin;el.className='fret-light';el.style.setProperty('--fret-color','#c4f46b');el.style.flex='1';el.textContent='D'+pin;
 $('scan-pins').append(el);
}
function renderScan(s){
 const scan=!!s?.scan_mode;document.body.classList.toggle('pin-scan',scan);$('scan-panel').hidden=!scan;
 const fresh=s?.connected&&s?.scan_last_frame&&Date.now()/1000-s.scan_last_frame<1.5;
 for(const pin of [17,16,18,21,15]){
  const value=s?.scan_pins?.[String(pin)],known=fresh&&value!==null&&value!==undefined;
  const el=$('scan-pin-'+pin);el.className='fret-light'+(known&&value?' pressed':'');el.textContent='D'+pin+' · '+(known?(value?'Apertado':'Solto'):'Sem leitura');
 }
}


for(const pin of [13,14,27,26]){
 const card=document.createElement('div');card.className='fret-test';card.style.setProperty('--fret-color','#b9c7dc');
 const title=document.createElement('strong');title.textContent='Canal D'+pin;
 const light=document.createElement('div');light.id='aux-light-'+pin;light.className='fret-light';light.textContent='Aguardando';
 const count=document.createElement('small');count.id='aux-count-'+pin;
 card.append(title,light,count);$('aux-channels').append(card);
}
function renderAux(s){
 for(const pin of [13,14,27,26]){
  const channel=s?.aux?.[String(pin)],known=s?.connected&&s?.aux_enabled&&!s?.bridge?.timed_out&&channel?.pressed!==null&&channel?.pressed!==undefined;
  $('aux-light-'+pin).className='fret-light'+(known&&channel.pressed?' pressed':'');
  $('aux-light-'+pin).textContent=known?(channel.pressed?'Apertado':'Solto'):'Sem leitura';
  $('aux-count-'+pin).textContent=channel?channel.presses+' apertos · '+channel.releases+' solturas':'Aguardando';
 }
 $('aux-hint').textContent=s?.aux_enabled?'Canais sem função atribuída: aperte somente o switch solicitado no chat.':'Aguardando firmware de canais e ligação em D13, D14, D27 e D26.';
}

async function post(url,data={}){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});if(!r.ok)throw Error('Falha ao salvar');return r.json()}
function toast(text){$('notice').textContent=text;$('notice').style.display='block';setTimeout(()=>$('notice').style.display='none',3000)}
function offline(text){renderAux(null);renderScan(last?{...last,connected:false}:null);renderFrets(null);$('whammy-value').textContent='Sem conexão';$('whammy-bar').value=0;$('whammy-range').textContent='Sem leitura atual';$('connection').textContent=text;$('connection').className='pill off';$('button-light').className='hardware-button';$('button-status').textContent='Estado desconhecido';$('button-hint').textContent='Aguardando dados reais da placa.';$('bridge-pill').textContent='○ Painel desconectado';$('bridge-pill').className='pill off';$('virtual-state').textContent='Desconhecido';$('strum-light').className='hardware-button';$('strum-status').textContent='Desconhecido';$('strum-hint').textContent='Sem dados atuais'}
function renderBridge(b){
if(!b)return;
$('bridge-pill').textContent=b.ready?'● Controle criado':'○ Acesso pendente';
$('bridge-pill').className='pill'+(b.ready?'':' off');
$('virtual-state').textContent=b.ready?('Máscara de botões: '+b.mask):'Indisponível';
$('virtual-sent').textContent=b.sent;
$('virtual-path').textContent=b.event_path?b.event_path+' · cinco cores':'Guitar Lab Virtual Controller · 2 botões';
$('bridge-detail').textContent=b.timed_out?'Sem atualização da placa há mais de 1,5 s: saída liberada.':b.error?'Não foi possível abrir o uinput: '+b.error+' · Execute a configuração de permissões documentada no README.':b.ready?'Cinco cores → botões independentes. Canais extras em identificação, sem saída para o jogo. Whammy D34 → ABS_Z.':'Aguardando acesso ao /dev/uinput.';
try{const pads=Array.from(navigator.getGamepads?.()||[]);const pad=pads.find(p=>p&&p.id.includes('Guitar Lab'));$('gamepad-state').textContent=pad?('Botões ativos: '+pad.buttons.filter(b=>b.pressed).length):'Não detectado';$('gamepad-hint').textContent=pad?pad.id:'Aperte o botão físico com esta página em foco; alguns navegadores não expõem o controle.';}catch(e){$('gamepad-state').textContent='Indisponível';$('gamepad-hint').textContent='Gamepad API não disponível neste navegador.'}
}
function render(s){renderAux(s);renderScan(s);last=s;renderBridge(s.bridge);renderFrets(s);
const analogKnown=s.connected&&!s.bridge?.timed_out&&Number.isInteger(s.whammy_raw);
$('whammy-value').textContent=analogKnown?Math.round(s.whammy_raw/4095*100)+'% · '+s.whammy_raw+' / 4095':'Aguardando leitura';
$('whammy-bar').value=analogKnown?s.whammy_raw:0;
$('whammy-range').textContent=analogKnown?'Menor observado: '+s.whammy_min+' · Maior observado: '+s.whammy_max+' · D34 → ABS_Z':'Sem dados analógicos atuais.';
const strumKnown=s.connected&&s.strum_pressed!==null&&s.strum_pressed!==undefined;
$('strum-light').className='hardware-button'+(strumKnown?(s.strum_pressed?' pressed':' ready'):'');
$('strum-status').textContent=strumKnown?(s.strum_pressed?'Pressionado':'Solto'):'Aguardando';
$('strum-hint').textContent=strumKnown?(s.strum_pressed?'LOW · D13 ligado ao GND':'HIGH · pull-up ativo'):'Esperando estado de D13.';
$('strum-count').textContent=(s.strum_presses||0)+' apertos · '+(s.strum_releases||0)+' solturas';
$('connection').textContent=s.connected?'● ESP32 conectado':'○ ESP32 desconectado';$('connection').className='pill'+(s.connected?'':' off');$('presses').textContent=s.presses;$('releases').textContent=s.releases;$('uptime').textContent=String(Math.floor(s.uptime/60)).padStart(2,'0')+':'+String(s.uptime%60).padStart(2,'0');const known=s.connected&&s.pressed!==null;$('button-light').className='hardware-button'+(known?(s.pressed?' pressed':' ready'):'');$('button-status').textContent=known?(s.pressed?'Pressionado':'Solto'):'Aguardando estado';$('button-hint').textContent=known?(s.pressed?'LOW · D21 conectado ao GND':'HIGH · pull-up interno ativo'):(s.error?'Verifique o cabo e a permissão da porta serial.':'Esperando a primeira leitura do firmware.');$('last').textContent=s.last_event?'Última leitura · '+new Date(s.last_event*1000).toLocaleTimeString('pt-BR'):'Sem evento de botão';$('device').textContent=(s.firmware||'ESP32 · aguardando identificação')+' · CH340';for(const [key] of stages){const input=$('check-'+key);if(document.activeElement!==input)input.checked=!!s.checks[key]}
const key=JSON.stringify(s.events);if(key!==historyKey){historyKey=key;$('events').replaceChildren();if(!s.events.length){const p=document.createElement('p');p.className='empty';p.textContent='Aguardando dados da placa…';$('events').append(p)}for(const ev of s.events){const row=document.createElement('div');row.className='event '+ev.kind;const time=document.createElement('time');time.textContent=new Date(ev.time).toLocaleTimeString('pt-BR',{hour12:false});const text=document.createElement('span');text.textContent=ev.message;row.append(time,text);$('events').append(row)}}}
async function poll(){if(fetching)return;fetching=true;try{const response=await fetch('/api/state',{signal:AbortSignal.timeout(2000)});if(!response.ok)throw Error();render(await response.json())}catch(e){offline('○ Painel sem conexão')}finally{fetching=false}}
$('reset').onclick=async()=>{try{await post('/api/reset');toast('Contagem zerada. Histórico preservado.');await poll()}catch(e){toast('Não foi possível iniciar a contagem.')}};
$('export').onclick=async()=>{try{const response=await fetch('/api/report');if(!response.ok)throw Error();const blob=new Blob([JSON.stringify(await response.json(),null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='guitar-lab-'+new Date().toISOString().slice(0,10)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Relatório exportado.')}catch(e){toast('Não foi possível exportar.')}};
for(const tab of document.querySelectorAll('[data-view]'))tab.onclick=()=>{for(const t of document.querySelectorAll('[data-view]'))t.setAttribute('aria-selected',String(t===tab));$('live').hidden=tab.dataset.view!=='live';$('journey').hidden=tab.dataset.view!=='journey'};
poll();setInterval(poll,100);
