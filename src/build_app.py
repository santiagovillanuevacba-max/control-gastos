#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA = json.load(open(ROOT/'data'/'processed'/'app_data.json', encoding='utf-8'))
DATA_JS = json.dumps(DATA, ensure_ascii=False)

HTML = r'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0b0f17">
<title>Control de Gastos · Santi</title>
<style>
:root{--bg:#0b0f17;--panel:#131a26;--panel2:#1b2432;--line:#25303f;--tx:#e8edf4;--tx2:#9fb0c3;--tx3:#6b7c90;
--accent:#4f9cff;--good:#2fbf87;--warn:#f2b34a;--bad:#f2685f;--chip:#20304a;--viol:#c9a9ff}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;background:var(--bg);color:var(--tx);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;font-size:15px;line-height:1.4}
.app{max-width:660px;margin:0 auto;padding:0 14px 100px}
header{position:sticky;top:0;background:linear-gradient(180deg,var(--bg) 72%,transparent);padding:15px 2px 9px;z-index:20}
h1{font-size:18px;margin:0;font-weight:700}
.sub{color:var(--tx3);font-size:12px;margin-top:2px}
.kpis{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin:4px 0 10px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:11px 12px}
.kpi .l{font-size:10.5px;color:var(--tx2);text-transform:uppercase;letter-spacing:.5px}
.kpi .v{font-size:19px;font-weight:700;margin-top:3px}
.kpi .n{font-size:10.5px;color:var(--tx3);margin-top:2px}
.kpi.big{grid-column:1/3}
.kpi.accent .v{color:var(--accent)}.kpi.bad .v{color:var(--bad)}.kpi.good .v{color:var(--good)}.kpi.warn .v{color:var(--warn)}
section{margin:15px 0}
.h2{font-size:12.5px;text-transform:uppercase;letter-spacing:.6px;color:var(--tx2);margin:0 0 8px 2px;display:flex;justify-content:space-between;align-items:center}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden}
.row{display:flex;align-items:center;gap:10px;padding:10px 13px;border-bottom:1px solid var(--line)}
.row:last-child{border-bottom:none}
.row .grow{flex:1;min-width:0}
.row .t{font-weight:600;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.row .m{font-size:11px;color:var(--tx3);margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.amt{font-variant-numeric:tabular-nums;font-weight:700;text-align:right;white-space:nowrap}
.amt.in{color:var(--good)}
.dot{width:9px;height:9px;border-radius:50%;flex:none}
.chev{color:var(--tx3);font-size:12px;transition:.15s}
.open .chev{transform:rotate(90deg)}
.sub-rows{display:none;background:#0e141f}
.open .sub-rows{display:block}
.sub-rows .row{padding-left:30px;background:transparent}
.chart{display:flex;flex-direction:column;gap:8px;padding:12px}
.cr{display:grid;grid-template-columns:82px 1fr auto;gap:8px;align-items:center;font-size:12.5px}
.cr .lab{color:var(--tx2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cr .val{font-variant-numeric:tabular-nums;font-weight:600}
.chbar{height:13px;border-radius:5px;background:var(--panel2);overflow:hidden}
.chbar>i{display:block;height:100%}
select,input,button{font-family:inherit;font-size:14px}
select,input[type=text],input[type=number],input[type=date]{background:var(--panel2);color:var(--tx);border:1px solid var(--line);border-radius:9px;padding:8px 9px;width:100%}
.mono{font-variant-numeric:tabular-nums}
.pill{font-size:10px;padding:2px 7px;border-radius:999px;background:var(--chip);color:var(--tx2);white-space:nowrap}
.pill.pend{background:#3a2f1c;color:var(--warn)}
.pill.mov{background:#22303f;color:var(--tx2)}
.tabbar{position:fixed;left:0;right:0;bottom:0;background:var(--panel);border-top:1px solid var(--line);display:flex;justify-content:space-around;padding:7px 4px calc(7px + env(safe-area-inset-bottom));z-index:30}
.tabbar button{background:none;border:none;color:var(--tx3);display:flex;flex-direction:column;align-items:center;gap:2px;font-size:10px;padding:3px 8px;flex:1}
.tabbar button.on{color:var(--accent)}
.tabbar .ic{font-size:18px;line-height:1}
.tab{display:none}.tab.on{display:block;animation:f .2s}
@keyframes f{from{opacity:0;transform:translateY(4px)}to{opacity:1}}
.note{background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:11px 13px;font-size:12.5px;color:var(--tx2)}
.note b{color:var(--tx)}
.catsel{background:var(--panel2);color:var(--warn);border:1px solid #3a2f1c;border-radius:8px;padding:6px 7px;font-size:12px;max-width:158px}
.catsel.done{color:var(--tx);border-color:#2f4a6b}
.btn{background:var(--accent);color:#fff;border:none;border-radius:9px;padding:10px 14px;width:100%;font-weight:600}
.btn2{background:var(--panel2);color:var(--tx);border:1px solid var(--line);border-radius:9px;padding:8px 12px;font-weight:600}
.seg{display:flex;gap:6px;overflow-x:auto;padding:2px 0 8px}
.seg button{background:var(--panel2);color:var(--tx2);border:1px solid var(--line);border-radius:999px;padding:6px 13px;white-space:nowrap}
.seg button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:9px}
label{font-size:11.5px;color:var(--tx2);display:block;margin:0 0 4px 2px}
.hint{font-size:11px;color:var(--tx3);margin-top:6px}
.badge{display:inline-block;font-size:10px;padding:1px 6px;border-radius:5px;background:var(--chip);color:var(--tx2);margin-left:6px}
.stack{display:flex;height:15px;border-radius:5px;overflow:hidden;background:var(--panel2)}
.stack>i{display:block;height:100%}
</style>
</head>
<body>
<div class="app">
  <header><h1>Control de Gastos</h1><div class="sub" id="hdr">Santi · datos ene–mar 2026 · web autónoma</div></header>

  <div class="tab on" id="tab-resumen">
    <div class="seg" id="r-months"></div>
    <div class="kpis" id="r-kpis"></div>
    <section><div class="h2">En qué se fue <span id="r-mlabel" style="text-transform:none;letter-spacing:0;color:var(--tx3)"></span></div>
      <div class="card"><div class="chart" id="r-cats"></div></div></section>
    <section><div class="h2">Gasto por mes</div><div class="card"><div class="chart" id="r-trend"></div></div></section>
    <section><div class="note" id="r-insight"></div></section>
  </div>

  <div class="tab" id="tab-mes">
    <div class="seg" id="m-months"></div>
    <section><div class="h2">Pendientes de categorizar <span id="m-pend-n" style="text-transform:none;letter-spacing:0;color:var(--warn)"></span></div>
      <div class="note" style="margin-bottom:8px">Tocá una para asignarle categoría. Al hacerlo, recuerdo a esa persona/comercio para las próximas.</div>
      <div class="card" id="m-pend"></div></section>
    <section><div class="h2">Gastos por categoría</div><div class="card" id="m-cats"></div></section>
    <section><div class="h2">Ingresos del mes</div><div class="card" id="m-inc"></div></section>
    <section><div class="h2">Movimientos internos (compensados)</div>
      <div class="note" id="m-mov"></div></section>
  </div>

  <div class="tab" id="tab-futuro">
    <section><div class="note" id="f-callout"></div></section>
    <section><div class="h2">Compromisos ya asumidos por mes</div>
      <div class="card"><div class="chart" id="f-chart"></div></div></section>
    <section><div class="h2">Detalle</div><div class="card" id="f-detail"></div>
      <div class="hint" style="padding:0 4px">Barra: <span style="color:var(--bad)">■</span> préstamo · <span style="color:var(--warn)">■</span> cuotas tarjeta · <span style="color:var(--viol)">■</span> fijos y suscripciones</div></section>
  </div>

  <div class="tab" id="tab-cargar">
    <section><div class="h2">Anotar un gasto al toque</div>
      <div class="card" style="padding:13px">
        <div class="grid2">
          <div><label>Monto</label><input type="number" id="q-amt" placeholder="$"></div>
          <div><label>Cuenta</label><select id="q-acc"><option>Efectivo</option><option>Mercado Pago</option><option>Visa débito</option><option>Dolar App</option></select></div>
        </div>
        <div style="margin-top:9px"><label>Categoría</label><select id="q-cat"></select></div>
        <div style="margin-top:9px"><label>Detalle (opcional)</label><input type="text" id="q-desc" placeholder="ej. café con Simón"></div>
        <button class="btn" style="margin-top:11px" onclick="addManual()">Guardar gasto</button>
        <div class="hint">Cuando llegue el resumen, si aparece este mismo gasto, el sistema lo concilia y no lo duplica.</div>
      </div>
      <div id="q-recent" style="margin-top:10px"></div>
    </section>
    <section><div class="h2">Memoria de destinatarios <span id="pm-n" style="text-transform:none;letter-spacing:0;color:var(--tx3)"></span></div>
      <div class="note" style="margin-bottom:8px">Reglas que aprendí de vos. Podés cambiarlas o borrarlas.</div>
      <div class="card" id="pm-list"></div></section>
  </div>
</div>

<nav class="tabbar" id="tabbar">
  <button class="on" data-tab="resumen"><span class="ic">📊</span>Resumen</button>
  <button data-tab="mes"><span class="ic">🗓️</span>Mes</button>
  <button data-tab="futuro"><span class="ic">🔮</span>Futuro</button>
  <button data-tab="cargar"><span class="ic">➕</span>Cargar</button>
</nav>

<script>
const DATA = __DATA__;
const F = n => '$'+Math.round(n).toLocaleString('es-AR');
const Fk = n => Math.abs(n)>=1e6?'$'+(n/1e6).toFixed(2)+'M':Math.abs(n)>=1e3?'$'+Math.round(n/1e3)+'k':'$'+Math.round(n);
const ML={'01':'Ene','02':'Feb','03':'Mar','04':'Abr','05':'May','06':'Jun','07':'Jul','08':'Ago','09':'Sep','10':'Oct','11':'Nov','12':'Dic'};
const monLabel=m=>ML[m.slice(5,7)]+' '+m.slice(2,4);

// ---- storage (safe, standalone). Data layer: swap this for a Google Sheet adapter later. ----
let MEM={};
const store={get(k){try{const v=localStorage.getItem(k);return v?JSON.parse(v):(k in MEM?MEM[k]:null)}catch(e){return MEM[k]??null}},
  set(k,v){MEM[k]=v;try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
let OV = store.get('ov')||{};        // txid -> "cat|subcat"
let PAY = store.get('pay')||{};      // payeeKey -> "cat|subcat"
let MAN = store.get('man')||[];      // manual entries

// ---- taxonomy select options ----
function catOptions(sel){
  let h='<option value="">— sin categoría —</option>';
  for(const[c,subs] of Object.entries(DATA.taxonomy)){
    h+=`<optgroup label="${c}">`;
    subs.forEach(s=>{const v=c+'|'+s;h+=`<option value="${v}" ${v===sel?'selected':''}>${s}</option>`});
    h+='</optgroup>';
  }
  return h;
}
// ---- payee key ----
function payeeKey(t){
  let d=(t.desc||'').replace(/transferencia (enviada|recibida)|pago con qr|pago de servicio|pago de suscripción|pago /gi,'').trim();
  d=d.replace(/\s+\d{3,}.*$/,'').trim();
  return d.toLowerCase().slice(0,32);
}
// ---- effective category ----
function catOf(t){
  if(OV[t.id]!==undefined) return OV[t.id];
  if(t.internal) return 'Movimiento|TRF Entre Cuentas';
  if(t.cat) return t.cat+'|'+t.subcat;
  const pk=payeeKey(t); if(PAY[pk]) return PAY[pk];
  return '';
}
const catName=v=>v?v.split('|')[0]:'';
const subName=v=>v?v.split('|')[1]:'';

// ---- money helpers ----
function expenseArs(t){
  if(t.internal) return 0;
  const v=catOf(t); if(catName(v)==='Ingresos'||catName(v)==='Movimiento'||catName(v)==='Ahorro & Inversiones') return 0;
  let a=0;
  if(t.kind==='consumo'){a+=(t.ars>0?t.ars:0);a+=(t.usd>0?t.usd*DATA.usd_rate:0);}
  else{a+=(t.ars<0?-t.ars:0);}
  return a;
}
function incomeArs(t){
  const v=catOf(t);
  if(catName(v)!=='Ingresos') return 0;
  return t.ars>0?t.ars:(t.kind==='consumo'&&t.ars<0?-t.ars:0);
}
const isFamily=t=>subName(catOf(t))==='Transferencia Personal';
const allTx=()=>DATA.tx.concat(MAN);
const MONTHS=DATA.months;

const COLORS={'Alimentación':'#4f9cff','Suscripciones':'#c9a9ff','Servicios financieros':'#ffab9f','Vivienda':'#7fe0c0','Impuestos & Tasas':'#f2d58a','Ocio & Entretenimiento':'#f2685f','Compras & Hogar':'#e59bd0','Transporte':'#5bd1e0','Salud & Bienestar':'#8ad97f','Educación & Desarrollo':'#b0a0ff','Mascotas':'#f0b27a','Viajes':'#7aa0f0','Otros/Imprevistos':'#8aa0b8','':'#6b7c90'};
const colorOf=c=>COLORS[c]||'#8aa0b8';

// ---- month expense by category ----
function monthCats(m){
  const o={};allTx().forEach(t=>{if(t.month!==m)return;const e=expenseArs(t);if(!e)return;const c=catName(catOf(t))||'Sin categoría';o[c]=(o[c]||0)+e;});return o;
}
function monthTotals(m){
  let gasto=0,propio=0,ayuda=0,pend=0;
  allTx().forEach(t=>{if(t.month!==m)return;
    gasto+=expenseArs(t);
    const inc=incomeArs(t); if(inc){if(isFamily(t))ayuda+=inc;else propio+=inc;}
    if(!t.internal && !catOf(t) && expenseArs(t)>0) pend++;
  });
  return {gasto,propio,ayuda,pend};
}

let curMonth=MONTHS[MONTHS.length-1];

// ================= RESUMEN =================
function segMonths(elId,cb){
  document.getElementById(elId).innerHTML=MONTHS.map(m=>`<button class="${m===curMonth?'on':''}" onclick="${cb}('${m}')">${monLabel(m)}</button>`).join('');
}
function setResMonth(m){curMonth=m;renderResumen();}
function renderResumen(){
  segMonths('r-months','setResMonth');
  const t=monthTotals(curMonth);
  const bal=t.propio+t.ayuda-t.gasto;
  document.getElementById('r-kpis').innerHTML=`
    <div class="kpi big ${bal>=0?'good':'bad'}"><div class="l">Balance de ${monLabel(curMonth)}</div><div class="v">${F(bal)}</div><div class="n">ingresos ${Fk(t.propio+t.ayuda)} − gastos ${Fk(t.gasto)}</div></div>
    <div class="kpi"><div class="l">Ingreso propio</div><div class="v">${Fk(t.propio)}</div><div class="n">tu plata</div></div>
    <div class="kpi warn"><div class="l">Ayuda familiar</div><div class="v">${Fk(t.ayuda)}</div><div class="n">de tu viejo</div></div>
    <div class="kpi accent"><div class="l">Gasto del mes</div><div class="v">${Fk(t.gasto)}</div></div>
    <div class="kpi ${t.pend?'warn':''}"><div class="l">Pendientes</div><div class="v">${t.pend}</div><div class="n">sin categoría</div></div>`;
  const cats=Object.entries(monthCats(curMonth)).sort((a,b)=>b[1]-a[1]);
  const mx=cats.length?cats[0][1]:1;
  document.getElementById('r-mlabel').textContent='· '+monLabel(curMonth);
  document.getElementById('r-cats').innerHTML=cats.map(([c,v])=>`<div class="cr"><span class="lab">${c}</span><span class="chbar"><i style="width:${Math.max(4,v/mx*100)}%;background:${colorOf(c)}"></i></span><span class="val">${Fk(v)}</span></div>`).join('')||'<div class="hint">Sin gastos categorizados aún</div>';
  const per={};allTx().forEach(t=>{if(!MONTHS.includes(t.month))return;const e=expenseArs(t);if(e)per[t.month]=(per[t.month]||0)+e;});
  const tmax=Math.max(...MONTHS.map(m=>per[m]||0),1);
  document.getElementById('r-trend').innerHTML=MONTHS.map(m=>`<div class="cr"><span class="lab">${monLabel(m)}</span><span class="chbar"><i style="width:${(per[m]||0)/tmax*100}%;background:var(--accent)"></i></span><span class="val">${Fk(per[m]||0)}</span></div>`).join('');
  const rec=Object.values(DATA.recurring).reduce((a,b)=>a+b,0);
  document.getElementById('r-insight').innerHTML=`<b>Tenés ${Fk(rec)}/mes en gastos fijos y suscripciones</b> que se repiten pase lo que pase. En <b>Futuro</b> ves cómo bajan tus compromisos cuando se termina el préstamo (julio). En <b>Mes</b> podés entrar al detalle de cada categoría.`;
}

// ================= MES =================
function setMesMonth(m){curMonth=m;renderMes();}
function renderMes(){
  segMonths('m-months','setMesMonth');
  const tx=allTx().filter(t=>t.month===curMonth);
  // pendientes
  const pend=tx.filter(t=>!t.internal && !catOf(t) && expenseArs(t)>0).sort((a,b)=>Math.abs(b.ars)-Math.abs(a.ars));
  document.getElementById('m-pend-n').textContent=pend.length?('· '+pend.length):'· 0 ✓';
  document.getElementById('m-pend').innerHTML=pend.length?pend.map(t=>rowCat(t)).join(''):'<div class="row"><div class="grow"><div class="t">Todo categorizado 🎉</div></div></div>';
  // categorias
  const groups={};tx.forEach(t=>{const e=expenseArs(t);if(!e)return;const c=catName(catOf(t))||'Sin categoría';(groups[c]=groups[c]||[]).push(t);});
  const order=Object.entries(groups).map(([c,items])=>[c,items.reduce((s,t)=>s+expenseArs(t),0),items]).sort((a,b)=>b[1]-a[1]);
  document.getElementById('m-cats').innerHTML=order.map(([c,tot,items],i)=>`
    <div id="cat-${i}"><div class="row" onclick="document.getElementById('cat-${i}').classList.toggle('open')" style="cursor:pointer">
      <span class="dot" style="background:${colorOf(c)}"></span>
      <div class="grow"><div class="t">${c}</div><div class="m">${items.length} mov.</div></div>
      <div class="amt">${F(tot)}</div><span class="chev">▶</span></div>
      <div class="sub-rows">${items.sort((a,b)=>expenseArs(b)-expenseArs(a)).map(t=>`
        <div class="row"><div class="grow"><div class="t">${cleanDesc(t)}</div><div class="m">${t.date.slice(8)}/${t.date.slice(5,7)} · ${t.account} · ${subName(catOf(t))}${t.cuota?' · cuota '+t.cuota:''}</div></div><div class="amt">${F(expenseArs(t))}</div></div>`).join('')}</div>
    </div>`).join('')||'<div class="row"><div class="t">Sin gastos</div></div>';
  // ingresos
  const inc=tx.filter(t=>incomeArs(t)>0);
  document.getElementById('m-inc').innerHTML=inc.map(t=>`<div class="row"><div class="grow"><div class="t">${cleanDesc(t)}</div><div class="m">${t.date.slice(8)}/${t.date.slice(5,7)} · ${isFamily(t)?'Ayuda familiar':subName(catOf(t))}</div></div><div class="amt in">+${F(incomeArs(t))}</div></div>`).join('')||'<div class="row"><div class="t">Sin ingresos</div></div>';
  // movimientos internos
  const mov=tx.filter(t=>t.internal);
  const movt=mov.reduce((s,t)=>s+Math.abs(t.ars),0)/2;
  document.getElementById('m-mov').innerHTML=`${mov.length} movimientos entre tus cuentas por <b>${F(movt)}</b> se compensan entre sí y no cuentan como gasto.`;
}
function cleanDesc(t){return (t.desc||'').replace(/\s+\d{4,}$/,'').slice(0,38);}
function rowCat(t){
  const cur=catOf(t);
  return `<div class="row"><div class="grow"><div class="t">${cleanDesc(t)}</div><div class="m">${t.date.slice(8)}/${t.date.slice(5,7)} · ${t.account} · ${F(Math.abs(t.ars))}</div></div>
    <select class="catsel ${cur?'done':''}" onchange="setCat('${t.id}',this.value)">${catOptions(cur)}</select></div>`;
}
function setCat(id,v){
  OV[id]=v;store.set('ov',OV);
  const t=allTx().find(x=>x.id===id);
  if(t && v){const pk=payeeKey(t);PAY[pk]=v;store.set('pay',PAY);
    // aplicar a otros pendientes del mismo destinatario (solo los que no tienen override)
    allTx().forEach(o=>{if(o.id!==id && !OV[o.id] && !o.internal && !o.cat && payeeKey(o)===pk){/* forward: se resolverá vía PAY en catOf */}});
  }
  renderMes();renderResumen();renderCargar();
}

// ================= FUTURO =================
function renderFuturo(){
  const fut=DATA.future;const mx=Math.max(...fut.map(f=>f.total));
  document.getElementById('f-chart').innerHTML=fut.map(f=>{
    const p=v=>v/f.total*100;
    return `<div class="cr"><span class="lab">${monLabel(f.month)}</span>
      <span class="stack" style="width:${f.total/mx*100}%">
        <i style="width:${p(f.prestamo)}%;background:var(--bad)"></i>
        <i style="width:${p(f.cuotas)}%;background:var(--warn)"></i>
        <i style="width:${p(f.recurrente)}%;background:var(--viol)"></i>
      </span><span class="val">${Fk(f.total)}</span></div>`;
  }).join('');
  document.getElementById('f-detail').innerHTML=fut.map(f=>`
    <div class="row"><div class="grow"><div class="t">${monLabel(f.month)}</div>
      <div class="m">${f.prestamo?'préstamo '+Fk(f.prestamo)+' · ':''}${f.cuotas?'cuotas '+Fk(f.cuotas)+' · ':''}fijos ${Fk(f.recurrente)}</div></div>
      <div class="amt">${F(f.total)}</div></div>`).join('');
  const drop=fut[0].total-fut[fut.length-1].total;
  document.getElementById('f-callout').innerHTML=`<b>En julio 2026 se termina el préstamo</b> y en septiembre las últimas cuotas de la Visa. Tus compromisos fijos bajan de ${Fk(fut[0].total)} a ${Fk(fut[fut.length-1].total)} por mes — son <b style="color:var(--good)">${Fk(drop)}/mes</b> que se te liberan para ahorrar o invertir.`;
}

// ================= CARGAR =================
function renderCargar(){
  document.getElementById('q-cat').innerHTML=catOptions('');
  // recientes manuales
  document.getElementById('q-recent').innerHTML = MAN.length?('<div class="card">'+MAN.slice(-6).reverse().map((t,i)=>`<div class="row"><div class="grow"><div class="t">${cleanDesc(t)||subName(catOf(t))||'Gasto'}</div><div class="m">${t.date.slice(8)}/${t.date.slice(5,7)} · ${t.account} · ${subName(OV[t.id]||'')}</div></div><div class="amt">${F(Math.abs(t.ars))}</div></div>`).join('')+'</div>'):'';
  // payee memory
  const keys=Object.keys(PAY);
  document.getElementById('pm-n').textContent=keys.length?('· '+keys.length):'';
  document.getElementById('pm-list').innerHTML=keys.length?keys.map(k=>`<div class="row"><div class="grow"><div class="t">${k}</div><div class="m">${subName(PAY[k])} · ${catName(PAY[k])}</div></div><button class="btn2" style="width:auto;padding:5px 10px" onclick="delPayee('${k.replace(/'/g,'')}')">✕</button></div>`).join(''):'<div class="row"><div class="t" style="color:var(--tx3)">Todavía no aprendí ninguna</div></div>';
}
function addManual(){
  const amt=+document.getElementById('q-amt').value;if(!amt){alert('Poné un monto');return;}
  const acc=document.getElementById('q-acc').value;const cat=document.getElementById('q-cat').value;
  const desc=document.getElementById('q-desc').value;
  let today;try{today=new Date().toISOString().slice(0,10);}catch(e){today=DATA.generated;}
  const id='man-'+MAN.length+'-'+Math.round(amt);
  const t={id,date:today,account:acc,desc:desc,ars:-Math.abs(amt),usd:0,cuota:'',kind:'manual',month:today.slice(0,7),internal:false,cat:'',subcat:'',isIncome:false,manual:true};
  MAN.push(t);store.set('man',MAN);
  if(cat){OV[id]=cat;store.set('ov',OV);}
  document.getElementById('q-amt').value='';document.getElementById('q-desc').value='';
  renderCargar();renderResumen();renderMes();
  alert('Gasto guardado ✓');
}
function delPayee(k){delete PAY[k];store.set('pay',PAY);renderCargar();renderMes();renderResumen();}

// ---- tabs ----
document.getElementById('tabbar').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;
  const tab=b.dataset.tab;document.querySelectorAll('.tabbar button').forEach(x=>x.classList.toggle('on',x===b));
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));document.getElementById('tab-'+tab).classList.add('on');
  if(tab==='mes')renderMes();if(tab==='futuro')renderFuturo();if(tab==='cargar')renderCargar();window.scrollTo(0,0);});

// encabezado dinámico según el rango real de meses cargados
if(MONTHS.length)document.getElementById('hdr').textContent=`Santi · ${monLabel(MONTHS[0])}–${monLabel(MONTHS[MONTHS.length-1])} · ${allTx().length} movimientos`;
renderResumen();renderFuturo();renderCargar();
</script>
</body>
</html>'''

HTML = HTML.replace('__DATA__', DATA_JS)
# Salida configurable: demo -> app/index.html (público); real -> ruta gitignored
# (ver run_pipeline.py). Así los datos reales nunca quedan en el HTML versionado.
_out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT/'app'/'index.html'
_out.parent.mkdir(parents=True, exist_ok=True)
open(_out,'w',encoding='utf-8').write(HTML)
print(f"[build_app] {_out.relative_to(ROOT)} generada ({round(len(HTML)/1024)} KB)")
