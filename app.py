import os
import json
import time
import sqlite3
import threading
import hmac
import hashlib
import requests
from urllib.parse import unquote
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32).hex())

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
DB_PATH = os.environ.get('DB_PATH', '')
if not DB_PATH or '://' in DB_PATH:
    DB_PATH = 'bot.db'
ADMIN_SECRET = os.environ.get('ADMIN_SECRET', 'ADMIN2024')
ADMIN_IDS = set(int(i) for i in os.environ.get('ADMIN_IDS', '').split(',') if i.strip().isdigit())
POLL_INTERVAL = 1

html_page = '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>CryptoArb</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0a0e17;--card:#131a2b;--accent:#00d4aa;--accent2:#6c5ce7;--text:#e2e8f0;--dim:#64748b;--danger:#ff4757;--border:#1e2a3a;--gradient:linear-gradient(135deg,#00d4aa,#6c5ce7)}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;overflow-x:hidden}
.app{max-width:480px;margin:0 auto;padding-bottom:80px;position:relative}
.header{padding:16px 20px;background:var(--card);border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:100}
.header img{width:42px;height:42px;border-radius:50%;border:2px solid var(--accent)}
.header-info h2{font-size:15px;font-weight:600}
.header-info span{font-size:12px;color:var(--dim)}
.page{display:none;padding:16px;animation:fadeIn .3s}
.page.active{display:block}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.card{background:var(--card);border-radius:16px;padding:16px;margin-bottom:12px;border:1px solid var(--border);transition:all .2s}
.card:active{transform:scale(.98)}
.bundle-card{cursor:pointer;position:relative;overflow:hidden}
.bundle-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--gradient)}
.bundle-pair{font-size:18px;font-weight:700;margin-bottom:8px;display:flex;align-items:center;gap:8px}
.bundle-pair .arrow{color:var(--accent);font-size:20px}
.bundle-profit{display:inline-block;background:rgba(0,212,170,.15);color:var(--accent);padding:4px 12px;border-radius:20px;font-size:14px;font-weight:600}
.bundle-meta{display:flex;justify-content:space-between;margin-top:12px;font-size:13px;color:var(--dim)}
.bundle-price{color:var(--text);font-weight:600}
.status-badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600}
.status-active{background:rgba(0,212,170,.15);color:var(--accent)}
.status-used{background:rgba(255,71,87,.15);color:var(--danger)}
.status-pending{background:rgba(108,92,231,.15);color:var(--accent2)}
.btn{width:100%;padding:14px;border:none;border-radius:12px;font-size:16px;font-weight:600;cursor:pointer;transition:all .2s}
.btn-primary{background:var(--gradient);color:#fff}
.btn-primary:active{opacity:.85;transform:scale(.98)}
.btn-danger{background:var(--danger);color:#fff}
.btn:disabled{opacity:.4;cursor:not-allowed}
.balance-box{background:var(--gradient);border-radius:16px;padding:20px;text-align:center;margin-bottom:16px}
.balance-box .label{font-size:13px;opacity:.8}
.balance-box .amount{font-size:32px;font-weight:700;margin-top:4px}
.balance-box .currency{font-size:14px;opacity:.7}
.input-group{margin-bottom:14px}
.input-group label{display:block;font-size:13px;color:var(--dim);margin-bottom:6px}
.input-group input,.input-group select,.input-group textarea{width:100%;padding:12px 14px;background:#0d1321;border:1px solid var(--border);border-radius:10px;color:var(--text);font-size:15px;outline:none;transition:border .2s}
.input-group input:focus,.input-group select:focus{border-color:var(--accent)}
.qr-box{background:#fff;border-radius:12px;padding:16px;text-align:center;margin:12px 0}
.qr-box canvas{max-width:200px}
.address-box{background:#0d1321;border-radius:10px;padding:12px;font-family:monospace;font-size:13px;word-break:break-all;text-align:center;cursor:pointer;border:1px solid var(--border);margin:12px 0;transition:all .2s}
.address-box:active{border-color:var(--accent);background:rgba(0,212,170,.05)}
.copy-hint{font-size:11px;color:var(--dim);text-align:center;margin-top:6px}
.network-badge{display:inline-block;background:rgba(0,212,170,.1);color:var(--accent);padding:4px 10px;border-radius:8px;font-size:12px;font-weight:600;margin-top:8px}
.history-item{display:flex;justify-content:space-between;align-items:center;padding:14px 0;border-bottom:1px solid var(--border)}
.history-item:last-child{border-bottom:none}
.history-left{display:flex;flex-direction:column;gap:4px}
.history-pair{font-weight:600;font-size:15px}
.history-date{font-size:12px;color:var(--dim)}
.history-right{text-align:right}
.history-profit{font-weight:600;color:var(--accent)}
.history-cost{font-size:12px;color:var(--dim)}
.profile-card{text-align:center;padding:24px}
.profile-avatar{width:80px;height:80px;border-radius:50%;border:3px solid var(--accent);margin:0 auto 12px}
.profile-name{font-size:20px;font-weight:700}
.profile-id{font-size:13px;color:var(--dim);margin-top:4px}
.profile-stats{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:20px}
.stat-box{background:#0d1321;border-radius:12px;padding:14px 8px}
.stat-val{font-size:20px;font-weight:700;color:var(--accent)}
.stat-lbl{font-size:11px;color:var(--dim);margin-top:4px}
.empty-state{text-align:center;padding:40px 20px;color:var(--dim)}
.empty-state .icon{font-size:48px;margin-bottom:12px}
.empty-state p{font-size:14px}
.nav{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:100%;max-width:480px;background:var(--card);border-top:1px solid var(--border);display:flex;padding:8px 0;z-index:100}
.nav-item{flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;padding:8px 0;cursor:pointer;transition:color .2s;color:var(--dim);font-size:10px;border:none;background:none}
.nav-item.active{color:var(--accent)}
.nav-item svg{width:24px;height:24px}
.modal-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.7);z-index:200;display:none;align-items:flex-end;justify-content:center}
.modal-overlay.show{display:flex}
.modal{background:var(--card);border-radius:20px 20px 0 0;width:100%;max-width:480px;padding:20px;max-height:80vh;overflow-y:auto;animation:slideUp .3s}
@keyframes slideUp{from{transform:translateY(100%)}to{transform:translateY(0)}}
.modal-handle{width:40px;height:4px;background:var(--border);border-radius:2px;margin:0 auto 16px}
.modal h3{font-size:18px;font-weight:700;margin-bottom:16px}
.toast{position:fixed;top:20px;left:50%;transform:translateX(-50%);background:var(--accent);color:#000;padding:10px 20px;border-radius:10px;font-size:14px;font-weight:600;z-index:300;opacity:0;transition:opacity .3s;pointer-events:none}
.toast.show{opacity:1}
.admin-section{background:#1a0a2e;border:1px solid #6c5ce7;border-radius:12px;padding:16px;margin-bottom:12px}
.admin-section h4{color:var(--accent2);margin-bottom:12px;font-size:15px}
.coin-icon{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;flex-shrink:0}
.coin-usdt{background:rgba(38,161,123,.2);color:#26a17b}
.coin-btc{background:rgba(247,147,26,.2);color:#f7911a}
.coin-eth{background:rgba(98,126,234,.2);color:#627eea}
</style>
</head>
<body>
<div id="toast" class="toast"></div>
<div class="app" id="app">
<div class="header">
<img id="hdrAvatar" src="" alt="">
<div class="header-info">
<h2 id="hdrName">Загрузка...</h2>
<span id="hdrStatus">Online</span>
</div>
</div>
<div id="previewBanner" style="display:none;background:#3d2c08;color:#fbbf24;padding:10px 16px;font-size:12px;text-align:center;border-bottom:1px solid #6b520f">⚠️ Демо-режим: открой приложение через бота (кнопка «Открыть Mini App» или /start), чтобы привязался твой Telegram-аккаунт и заработала админка.</div>

<div class="page active" id="pageBundles">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
<h3 style="font-size:20px;font-weight:700">Связки</h3>
<span style="font-size:12px;color:var(--dim)" id="bundleCount">0 связок</span>
</div>
<div id="bundlesList"></div>
</div>

<div class="page" id="pageDeposit">
<h3 style="font-size:20px;font-weight:700;margin-bottom:16px">Пополнение</h3>
<div class="balance-box">
<div class="label">Баланс</div>
<div class="amount" id="balDeposit">0.00</div>
<div class="currency">USDT</div>
</div>
<div class="card">
<div style="text-align:center;margin-bottom:12px">
<div style="font-size:14px;color:var(--dim)">Отправьте USDT на адрес</div>
<div class="network-badge" id="netBadge">TRC-20</div>
</div>
<div class="address-box" id="depositAddress" onclick="copyAddress()"></div>
<div class="copy-hint">Нажмите чтобы скопировать</div>
</div>
<div class="card" style="text-align:center">
<div style="font-size:13px;color:var(--dim)">Минимальное пополнение</div>
<div style="font-size:18px;font-weight:600;margin-top:4px">10 USDT</div>
</div>
</div>

<div class="page" id="pageWithdraw">
<h3 style="font-size:20px;font-weight:700;margin-bottom:16px">Вывод</h3>
<div class="balance-box">
<div class="label">Доступно</div>
<div class="amount" id="balWithdraw">0.00</div>
<div class="currency">USDT</div>
</div>
<div class="card">
<div class="input-group">
<label>Адрес кошелька (TRC-20)</label>
<input type="text" id="withdrawAddr" placeholder="T...">
</div>
<div class="input-group">
<label>Сумма USDT</label>
<input type="number" id="withdrawAmount" placeholder="0.00" step="0.01" min="0">
</div>
<button class="btn btn-primary" onclick="doWithdraw()">Вывести</button>
<div style="margin-top:12px;text-align:center;font-size:12px;color:var(--dim)">Минимум: 10 USDT | Комиссия: 1 USDT</div>
</div>
</div>

<div class="page" id="pageHistory">
<h3 style="font-size:20px;font-weight:700;margin-bottom:16px">История</h3>
<div id="historyList"></div>
</div>

<div class="page" id="pageProfile">
<div class="card profile-card">
<img class="profile-avatar" id="profAvatar" src="" alt="">
<div class="profile-name" id="profName"></div>
<div class="profile-id" id="profId"></div>
<div class="profile-stats">
<div class="stat-box"><div class="stat-val" id="statBundles">0</div><div class="stat-lbl">Связок</div></div>
<div class="stat-box"><div class="stat-val" id="statProfit">0</div><div class="stat-lbl">Прибыль $</div></div>
<div class="stat-box"><div class="stat-val" id="statBalance">0</div><div class="stat-lbl">Баланс $</div></div>
</div>
</div>
<div class="card" style="text-align:center">
<div style="font-size:12px;color:var(--dim)">CryptoArb Mini App v1.0</div>
</div>
</div>

<div id="adminPanel" style="display:none">
<div class="page active">
<h3 style="font-size:20px;font-weight:700;margin-bottom:16px;color:var(--accent2)">Админ панель</h3>
<div class="admin-section">
<h4>Статистика</h4>
<div id="adminStats" style="display:grid;grid-template-columns:1fr 1fr;gap:8px"></div>
</div>
<div class="admin-section">
<h4>Адрес пополнения</h4>
<div class="input-group">
<label>TRC-20 адрес</label>
<input type="text" id="adminAddr" placeholder="T...">
</div>
<button class="btn btn-primary" onclick="adminUpdateAddr()" style="margin-top:8px">Сохранить адрес</button>
</div>
<div class="admin-section">
<h4>Новая связка</h4>
<div class="input-group"><label>Валюта 1</label><input type="text" id="adminCoin1" placeholder="BTC"></div>
<div class="input-group"><label>Валюта 2</label><input type="text" id="adminCoin2" placeholder="USDT"></div>
<div class="input-group"><label>Биржа покупки</label><input type="text" id="adminEx1" placeholder="Binance"></div>
<div class="input-group"><label>Биржа продажи</label><input type="text" id="adminEx2" placeholder="Bybit"></div>
<div class="input-group"><label>Прибыль %</label><input type="number" id="adminProfit" placeholder="2.5" step="0.1"></div>
<div class="input-group"><label>Стоимость связки USDT</label><input type="number" id="adminPrice" placeholder="100" step="1"></div>
<button class="btn btn-primary" onclick="adminAddBundle()" style="margin-top:8px">Добавить связку</button>
</div>
<div class="admin-section">
<h4>Управление связками</h4>
<div id="adminBundleList"></div>
</div>
<div class="admin-section">
<h4>Пользователи</h4>
<div style="display:flex;flex-direction:column;gap:6px;margin-bottom:10px">
<input type="number" id="adminTopUpId" placeholder="ID пользователя" style="width:100%;padding:10px 12px;background:#0d1321;border:1px solid var(--border);border-radius:8px;color:var(--text)">
<div style="display:flex;gap:6px">
<input type="number" id="adminTopUpAmount" placeholder="Сумма USDT" style="flex:1;padding:10px 12px;background:#0d1321;border:1px solid var(--border);border-radius:8px;color:var(--text)">
<button onclick="adminTopUp()" style="background:var(--accent);color:#000;border:none;padding:10px 14px;border-radius:8px;font-weight:600;cursor:pointer">Пополнить</button>
</div>
</div>
<div id="adminUsersList"></div>
</div>
<div class="admin-section">
<h4>Заявки на вывод</h4>
<div id="adminWithdrawalsList"></div>
</div>
<button class="btn btn-danger" onclick="exitAdmin()" style="margin-top:12px">Выйти из админки</button>
</div>
</div>
</div>

<nav class="nav" id="mainNav">
<button class="nav-item active" onclick="showPage('Bundles')" data-page="Bundles">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
<span>Связки</span>
</button>
<button class="nav-item" onclick="showPage('Deposit')" data-page="Deposit">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M2 12h20"/></svg>
<span>Пополнить</span>
</button>
<button class="nav-item" onclick="showPage('Withdraw')" data-page="Withdraw">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>
<span>Вывод</span>
</button>
<button class="nav-item" onclick="showPage('History')" data-page="History">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
<span>История</span>
</button>
<button class="nav-item" onclick="showPage('Profile')" data-page="Profile">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
<span>Профиль</span>
</button>
</nav>

<div class="modal-overlay" id="bundleModal">
<div class="modal">
<div class="modal-handle"></div>
<h3 id="modalTitle">Связка</h3>
<div id="modalContent"></div>
</div>
</div>

<script>
let tg=window.Telegram?.WebApp;
let user=null;
let balance=0;
let isAdmin=false;
let isTelegramUser=false;
let pollTimer=null;

function init(){
if(tg){tg.ready();tg.expand();if(tg.setHeaderColor)tg.setHeaderColor('#0a0e17');if(tg.setBackgroundColor)tg.setBackgroundColor('#0a0e17')}
let ud=tg?.initDataUnsafe?.user;
if(!ud){
ud={id:12345678,first_name:'Test',last_name:'User',username:'testuser',photo_url:'https://ui-avatars.com/api/?name=T&background=00d4aa&color=fff&size=128'};
}
user=ud;
let realClient=!!(tg&&tg.initDataUnsafe&&tg.initDataUnsafe.user);
let rawInit=tg?.initData||'';
fetch('/api/init',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:user.id,first_name:user.first_name,last_name:user.last_name||'',username:user.username||'',photo_url:user.photo_url||'',initData:rawInit})}).then(r=>r.json()).then(d=>{
isTelegramUser=(!!d.is_telegram)||realClient;
balance=d.balance||0;
isAdmin=d.is_admin||false;
if(d.user&&d.user.id){user=d.user}
let nameText=[user.first_name,user.last_name].filter(Boolean).join(' ')||'Пользователь';
document.getElementById('hdrAvatar').src=user.photo_url||'';
document.getElementById('hdrName').textContent=nameText;
document.getElementById('profAvatar').src=user.photo_url||'';
document.getElementById('profName').textContent=nameText;
document.getElementById('profId').textContent='ID: '+(isTelegramUser?user.id:'не определен (демо)');
if(!isTelegramUser)document.getElementById('previewBanner').style.display='block';
if(isAdmin)renderAdmin();
loadAll();
startPoll();
});
}

function showPage(name){
document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
document.getElementById('page'+name).classList.add('active');
document.querySelectorAll('.nav-item').forEach(n=>{n.classList.toggle('active',n.dataset.page===name)});
if(name==='Bundles')loadBundles();
if(name==='Deposit')loadDeposit();
if(name==='Withdraw')loadWithdraw();
if(name==='History')loadHistory();
if(name==='Profile')loadProfile();
}

function toast(msg){
let t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');
setTimeout(()=>t.classList.remove('show'),2500);
}

function loadAll(){loadBundles();loadDeposit();loadWithdraw();loadProfile();}

function loadBundles(){
fetch('/api/bundles').then(r=>r.json()).then(d=>{
let c=document.getElementById('bundlesList');
document.getElementById('bundleCount').textContent=d.length+' связок';
if(!d.length){c.innerHTML='<div class="empty-state"><div class="icon">📊</div><p>Нет доступных связок</p></div>';return}
c.innerHTML=d.map(b=>'<div class="card bundle-card" onclick="showBundle('+b.id+')"><div class="bundle-pair"><span>'+b.coin1+'</span><span class="arrow">→</span><span>'+b.coin2+'</span></div><div style="margin-bottom:8px"><span style="font-size:12px;color:var(--dim)">'+b.exchange1+' → '+b.exchange2+'</span></div><div class="bundle-profit">+'+b.profit+'%</div><div class="bundle-meta"><span>Стоимость</span><span class="bundle-price">'+b.price+' USDT</span></div></div>').join('');
});
}

function showBundle(id){
fetch('/api/bundles').then(r=>r.json()).then(d=>{
let b=d.find(x=>x.id===id);if(!b)return;
let canBuy=balance>=b.price;
document.getElementById('modalTitle').textContent=b.coin1+' → '+b.coin2;
document.getElementById('modalContent').innerHTML=
'<div style="margin-bottom:16px"><div style="font-size:13px;color:var(--dim);margin-bottom:4px">Направление</div><div style="font-size:16px;font-weight:600">'+b.coin1+' на '+b.coin2+'</div></div>'+
'<div style="margin-bottom:16px"><div style="font-size:13px;color:var(--dim);margin-bottom:4px">Биржи</div><div style="font-size:16px;font-weight:600">'+b.exchange1+' → '+b.exchange2+'</div></div>'+
'<div style="margin-bottom:16px"><div style="font-size:13px;color:var(--dim);margin-bottom:4px">Прибыль</div><div class="bundle-profit" style="font-size:20px">+'+b.profit+'%</div></div>'+
'<div style="margin-bottom:16px"><div style="font-size:13px;color:var(--dim);margin-bottom:4px">Стоимость связки</div><div style="font-size:18px;font-weight:700">'+b.price+' USDT</div></div>'+
'<div style="margin-bottom:16px"><div style="font-size:13px;color:var(--dim);margin-bottom:4px">Ваш баланс</div><div style="font-size:16px;font-weight:600;color:'+(canBuy?'var(--accent)':'var(--danger)')+'">'+balance.toFixed(2)+' USDT</div></div>'+
'<button class="btn btn-primary" onclick="buyBundle('+b.id+')" '+(canBuy?'':'disabled')+'>'+(canBuy?'Купить связку':'Недостаточно средств')+'</button>';
document.getElementById('bundleModal').classList.add('show');
});
}

function buyBundle(id){
fetch('/api/buy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:user.id,bundle_id:id})}).then(r=>r.json()).then(d=>{
document.getElementById('bundleModal').classList.remove('show');
if(d.ok){toast('Связка куплена! Прибыль: +'+d.profit+' USDT');balance=d.new_balance;updateBalances();loadHistory();}
else toast(d.error||'Ошибка');
});
}

function loadDeposit(){
fetch('/api/settings').then(r=>r.json()).then(d=>{
let addr=d.deposit_address||'Ожидается...';
document.getElementById('depositAddress').textContent=addr;
document.getElementById('netBadge').textContent=d.network||'TRC-20';
document.getElementById('balDeposit').textContent=balance.toFixed(2);
});
}

function copyAddress(){
let addr=document.getElementById('depositAddress').textContent;
if(navigator.clipboard)navigator.clipboard.writeText(addr);
toast('Адрес скопирован!');
if(tg?.HapticFeedback)tg.HapticFeedback.notificationOccurred('success');
}

function loadWithdraw(){document.getElementById('balWithdraw').textContent=balance.toFixed(2)}

function doWithdraw(){
let addr=document.getElementById('withdrawAddr').value.trim();
let amount=parseFloat(document.getElementById('withdrawAmount').value);
if(!addr){toast('Введите адрес');return}
fetch('/api/withdraw',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:user.id,address:addr,amount:amount})}).then(r=>r.json()).then(d=>{
if(d.admin){
isAdmin=true;
document.getElementById('mainNav').style.display='none';
document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
document.getElementById('adminPanel').style.display='block';
renderAdmin();
toast('Админ панель активирована');
}
else if(d.ok){toast('Заявка на вывод создана');balance=d.new_balance;updateBalances();loadHistory();document.getElementById('withdrawAddr').value='';document.getElementById('withdrawAmount').value='';}
else toast(d.error||'Ошибка');
});
}

function loadHistory(){
fetch('/api/history?user_id='+user.id).then(r=>r.json()).then(d=>{
let c=document.getElementById('historyList');
if(!d.length){c.innerHTML='<div class="empty-state"><div class="icon">📋</div><p>История пуста</p></div>';return}
c.innerHTML=d.map(h=>'<div class="card"><div class="history-item"><div class="history-left"><div class="history-pair">'+h.coin1+' → '+h.coin2+'</div><div class="history-date">'+h.date+'</div></div><div class="history-right"><div class="history-profit">+'+h.profit+' USDT</div><div class="history-cost">'+h.cost+' USDT</div></div></div></div>').join('');
});
}

function loadProfile(){
document.getElementById('profAvatar').src=user.photo_url||'';
document.getElementById('profName').textContent=[user.first_name,user.last_name].filter(Boolean).join(' ');
document.getElementById('profId').textContent='ID: '+user.id;
fetch('/api/profile?user_id='+user.id).then(r=>r.json()).then(d=>{
document.getElementById('statBundles').textContent=d.total_bundles||0;
document.getElementById('statProfit').textContent=(d.total_profit||0).toFixed(1);
document.getElementById('statBalance').textContent=(d.balance||0).toFixed(1);
});
}

function updateBalances(){
document.getElementById('balDeposit').textContent=balance.toFixed(2);
document.getElementById('balWithdraw').textContent=balance.toFixed(2);
}

function renderAdmin(){
fetch('/api/settings').then(r=>r.json()).then(d=>{
document.getElementById('adminAddr').value=d.deposit_address||'';
});
fetch('/api/bundles').then(r=>r.json()).then(d=>{
let c=document.getElementById('adminBundleList');
if(!d.length){c.innerHTML='<div style="color:var(--dim);font-size:13px;text-align:center;padding:12px">Нет связок</div>';return}
c.innerHTML=d.map(b=>'<div style="padding:10px 0;border-bottom:1px solid var(--border)"><div style="display:flex;justify-content:space-between;align-items:center"><div><div style="font-weight:600">'+b.coin1+' → '+b.coin2+'</div><div style="font-size:12px;color:var(--dim)">'+b.exchange1+' → '+b.exchange2+'</div></div><div style="display:flex;gap:6px"><button onclick="adminEditBundle('+b.id+')" style="background:var(--accent2);color:#fff;border:none;padding:6px 10px;border-radius:8px;font-size:12px;cursor:pointer">Изменить</button><button onclick="adminDelBundle('+b.id+')" style="background:var(--danger);color:#fff;border:none;padding:6px 10px;border-radius:8px;font-size:12px;cursor:pointer">Удалить</button></div></div><div id="editRow-'+b.id+'" style="display:none;margin-top:10px"><div style="display:flex;gap:8px;flex-wrap:wrap"><div style="flex:1;min-width:100px"><label style="font-size:11px;color:var(--dim)">Прибыль %</label><input type="number" id="editProfit-'+b.id+'" value="'+b.profit+'" style="width:100%;padding:8px;background:#0d1321;border:1px solid var(--border);border-radius:8px;color:var(--text);font-size:14px"></div><div style="flex:1;min-width:100px"><label style="font-size:11px;color:var(--dim)">Цена USDT</label><input type="number" id="editPrice-'+b.id+'" value="'+b.price+'" style="width:100%;padding:8px;background:#0d1321;border:1px solid var(--border);border-radius:8px;color:var(--text);font-size:14px"></div><button onclick="adminSaveBundle('+b.id+')" style="background:var(--accent);color:#000;border:none;padding:8px 14px;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;align-self:flex-end">Сохранить</button></div></div></div>').join('');
});
renderAdminStats();
renderAdminUsers();
renderAdminWithdrawals();
}

function adminStatBox(v,l){
return '<div style="background:#0d1321;border-radius:10px;padding:14px 10px;text-align:center"><div style="font-size:20px;font-weight:700;color:var(--accent)">'+v+'</div><div style="font-size:11px;color:var(--dim);margin-top:4px">'+l+'</div></div>';
}

function renderAdminStats(){
fetch('/api/admin/stats?user_id='+user.id).then(r=>r.json()).then(d=>{
if(d.error)return;
document.getElementById('adminStats').innerHTML=
adminStatBox(d.users||0,'Пользователей')+
adminStatBox((d.volume||0).toFixed(1),'Объём, USDT')+
adminStatBox((d.profit||0).toFixed(1),'Прибыль платформы')+
adminStatBox(d.pending||0,'Заявок к выводу');
});
}

function adminName(u){return [u.first_name,u.last_name].filter(Boolean).join(' ')||u.username||('Пользователь '+u.id)}

function renderAdminUsers(){
fetch('/api/admin/users?user_id='+user.id).then(r=>r.json()).then(d=>{
let c=document.getElementById('adminUsersList');
if(d.error){c.innerHTML='<div style="color:var(--dim);font-size:13px;text-align:center;padding:12px">Нет доступа</div>';return}
if(!d.length){c.innerHTML='<div style="color:var(--dim);font-size:13px;text-align:center;padding:12px">Нет пользователей</div>';return}
c.innerHTML=d.map(u=>'<div style="padding:10px 0;border-bottom:1px solid var(--border)"><div style="display:flex;justify-content:space-between;align-items:center"><div><div style="font-weight:600">'+u.name+(u.is_admin?' <span style="color:#6c5ce7;background:rgba(108,92,231,.15);padding:2px 8px;border-radius:8px;font-size:11px">админ</span>':'')+'</div><div style="font-size:12px;color:var(--dim)">ID '+u.id+' | @'+(u.username||'-')+'</div></div><div style="text-align:right"><div style="font-weight:700;color:var(--accent)">'+u.balance.toFixed(2)+'</div><div style="font-size:11px;color:var(--dim)">USDT</div></div></div><div style="display:flex;justify-content:flex-end;gap:6px;margin-top:8px"><button onclick="adminToggleAdmin('+u.id+')" style="background:#0d1321;color:var(--text);border:1px solid var(--border);padding:6px 10px;border-radius:8px;font-size:12px;cursor:pointer">'+(u.is_admin?'Снять админа':'Сделать админом')+'</button></div></div>').join('');
});
}

function adminTopUp(){
let tuid=parseInt(document.getElementById('adminTopUpId').value);
let amt=parseFloat(document.getElementById('adminTopUpAmount').value);
if(!tuid){toast('Введите ID пользователя');return}
if(!amt||amt<=0){toast('Введите сумму');return}
fetch('/api/admin/user',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:user.id,target_id:tuid,action:'add_balance',amount:amt})}).then(r=>r.json()).then(d=>{
if(d.ok){toast('Баланс пополнен');document.getElementById('adminTopUpId').value='';document.getElementById('adminTopUpAmount').value='';renderAdminUsers()}else toast(d.error||'Ошибка');
});
}

function adminToggleAdmin(tuid){
fetch('/api/admin/user',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:user.id,target_id:tuid,action:'toggle_admin'})}).then(r=>r.json()).then(d=>{
if(d.ok){toast('Права обновлены');renderAdminUsers()}else toast(d.error||'Ошибка');
});
}

function renderAdminWithdrawals(){
fetch('/api/admin/withdrawals?user_id='+user.id).then(r=>r.json()).then(d=>{
let c=document.getElementById('adminWithdrawalsList');
if(d.error){c.innerHTML='<div style="color:var(--dim);font-size:13px;text-align:center;padding:12px">Нет доступа</div>';return}
if(!d.length){c.innerHTML='<div style="color:var(--dim);font-size:13px;text-align:center;padding:12px">Заявок на вывод нет</div>';return}
c.innerHTML=d.map(w=>'<div style="padding:10px 0;border-bottom:1px solid var(--border)"><div style="display:flex;justify-content:space-between;align-items:center"><div><div style="font-weight:600;font-size:14px">'+w.name+'</div><div style="font-size:12px;color:var(--dim);word-break:break-all">'+w.address+'</div></div><div style="text-align:right"><div style="font-weight:700;color:var(--accent)">'+w.amount.toFixed(2)+' USDT</div><div style="font-size:11px;color:var(--dim)">'+w.created_at+'</div></div></div><div style="margin-top:8px">'+(w.status==='pending'?'<div style="display:flex;gap:6px"><button data-id="'+w.id+'" data-act="approve" onclick="adminWithdrawal(this.dataset.id,this.dataset.act)" style="flex:1;background:var(--accent);color:#000;border:none;padding:8px;border-radius:8px;font-weight:600;font-size:13px;cursor:pointer">Одобрить</button><button data-id="'+w.id+'" data-act="reject" onclick="adminWithdrawal(this.dataset.id,this.dataset.act)" style="flex:1;background:var(--danger);color:#fff;border:none;padding:8px;border-radius:8px;font-weight:600;font-size:13px;cursor:pointer">Отклонить</button></div>':'<div style="font-size:12px;color:var(--dim)">'+w.status+'</div>')+'</div></div>').join('');
});
}

function adminWithdrawal(wid,action){
fetch('/api/admin/withdrawal',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:user.id,id:wid,action:action})}).then(r=>r.json()).then(d=>{
if(d.ok){toast(action==='approve'?'Вывод одобрен':'Вывод отклонён, баланс возвращён');renderAdminWithdrawals();renderAdminStats()}else toast(d.error||'Ошибка');
});
}

function adminUpdateAddr(){
let addr=document.getElementById('adminAddr').value.trim();
fetch('/api/admin/addr',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:user.id,address:addr})}).then(r=>r.json()).then(d=>{
if(d.ok)toast('Адрес обновлён');else toast(d.error||'Ошибка');
});
}

function adminAddBundle(){
let d={user_id:user.id,coin1:document.getElementById('adminCoin1').value.trim(),coin2:document.getElementById('adminCoin2').value.trim(),exchange1:document.getElementById('adminEx1').value.trim(),exchange2:document.getElementById('adminEx2').value.trim(),profit:parseFloat(document.getElementById('adminProfit').value)||0,price:parseFloat(document.getElementById('adminPrice').value)||0};
if(!d.coin1||!d.coin2){toast('Заполните валюты');return}
fetch('/api/admin/bundle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}).then(r=>r.json()).then(r=>{
if(r.ok){toast('Связка добавлена');renderAdmin();['adminCoin1','adminCoin2','adminEx1','adminEx2','adminProfit','adminPrice'].forEach(id=>document.getElementById(id).value='')}
else toast(r.error||'Ошибка');
});
}

function adminEditBundle(id){
let el=document.getElementById('editRow-'+id);
el.style.display=el.style.display==='none'?'flex':'none';
}

function adminSaveBundle(id){
let profit=parseFloat(document.getElementById('editProfit-'+id).value)||0;
let price=parseFloat(document.getElementById('editPrice-'+id).value)||0;
serviceAdminBundle(id,{profit:profit,price:price},'Связка обновлена');
}

function serviceAdminBundle(id,data,msg){
fetch('/api/admin/bundle/'+id,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.assign({user_id:user.id},data))}).then(r=>r.json()).then(d=>{
if(d.ok){toast(msg);renderAdmin()}else toast(d.error||'Ошибка');
});
}

function adminDelBundle(id){
serviceAdminBundle(id,{action:'delete'},'Удалено');
}

function exitAdmin(){
isAdmin=false;
document.getElementById('adminPanel').style.display='none';
document.getElementById('mainNav').style.display='flex';
showPage('Bundles');
}

function startPoll(){
if(pollTimer)clearInterval(pollTimer);
pollTimer=setInterval(()=>{
fetch('/api/balance?user_id='+user.id).then(r=>r.json()).then(d=>{
if(d.balance!==undefined){balance=d.balance;updateBalances()}
});
loadDeposit();
if(!document.getElementById('bundleModal').classList.contains('show'))loadBundles();
},5000);
}

document.getElementById('bundleModal').addEventListener('click',function(e){if(e.target===this)this.classList.remove('show')});

init();
</script>
</body>
</html>'''

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    global DB_PATH
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
    except Exception as e:
        print("DB PATH ERROR:", e, "- falling back to bot.db in current dir")
        DB_PATH = 'bot.db'
        conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            username TEXT DEFAULT '',
            photo_url TEXT DEFAULT '',
            balance REAL DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS bundles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin1 TEXT NOT NULL,
            coin2 TEXT NOT NULL,
            exchange1 TEXT NOT NULL,
            exchange2 TEXT NOT NULL,
            profit REAL DEFAULT 0,
            price REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            bundle_id INTEGER NOT NULL,
            profit REAL DEFAULT 0,
            cost REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (bundle_id) REFERENCES bundles(id)
        );
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            address TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    ''')
    if not conn.execute("SELECT value FROM settings WHERE key='deposit_address'").fetchone():
        conn.execute("INSERT INTO settings (key,value) VALUES (?,?)", ('deposit_address', ''))
    if not conn.execute("SELECT value FROM settings WHERE key='network'").fetchone():
        conn.execute("INSERT INTO settings (key,value) VALUES (?,?)", ('network', 'TRC-20'))
    if not conn.execute("SELECT COUNT(*) as c FROM bundles").fetchone()['c']:
        conn.executemany("INSERT INTO bundles (coin1,coin2,exchange1,exchange2,profit,price) VALUES (?,?,?,?,?,?)", [
            ('BTC', 'USDT', 'Binance', 'Bybit', 2.5, 100),
            ('ETH', 'USDT', 'OKX', 'KuCoin', 1.8, 50),
            ('BNB', 'USDT', 'Binance', 'Gate.io', 3.2, 75),
        ])
    conn.commit()
    conn.close()

def ensure_user(uid, first_name='', last_name='', username='', photo_url=''):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not row:
        is_admin = 1 if ADMIN_IDS and uid in ADMIN_IDS else 0
        conn.execute("INSERT INTO users (id,first_name,last_name,username,photo_url,is_admin) VALUES (?,?,?,?,?,?)",
                     (uid, first_name, last_name, username, photo_url, is_admin))
        conn.commit()
    else:
        if ADMIN_IDS and uid in ADMIN_IDS and not row['is_admin']:
            conn.execute("UPDATE users SET is_admin=1 WHERE id=?", (uid,))
        if first_name and first_name != row['first_name']:
            conn.execute("UPDATE users SET first_name=? WHERE id=?", (first_name, uid))
        if last_name and last_name != row['last_name']:
            conn.execute("UPDATE users SET last_name=? WHERE id=?", (last_name, uid))
        if username and username != row['username']:
            conn.execute("UPDATE users SET username=? WHERE id=?", (username, uid))
        if photo_url and photo_url != row['photo_url']:
            conn.execute("UPDATE users SET photo_url=? WHERE id=?", (photo_url, uid))
        conn.commit()
    conn.close()

def is_admin_user(uid):
    conn = get_db()
    row = conn.execute("SELECT is_admin FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return row and row['is_admin'] == 1

def validate_init_data(init_data):
    if not BOT_TOKEN or not init_data:
        return None
    raw = {}
    for part in init_data.split('&'):
        if '=' not in part:
            continue
        k, v = part.split('=', 1)
        raw[k] = v
    if 'hash' not in raw or 'user' not in raw:
        return None
    received = raw.get('hash') or ''
    data_check = '\n'.join(f'{k}={v}' for k, v in sorted(raw.items()) if k != 'hash')
    secret = hmac.new(key=b'WebAppData', msg=BOT_TOKEN.encode(), digestmod=hashlib.sha256).digest()
    calc = hmac.new(key=secret, msg=data_check.encode(), digestmod=hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc, received):
        return None
    try:
        user = json.loads(unquote(raw['user']))
    except Exception:
        return None
    return user

@app.route('/')
def index():
    return html_page, 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/<path:anypath>')
def catch_all(anypath):
    return html_page, 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.errorhandler(404)
def not_found(e):
    return html_page, 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/healthz')
def healthz():
    return jsonify({'status': 'ok', 'db': DB_PATH})

@app.route('/api/init', methods=['POST'])
def api_init():
    d = request.json
    real = None
    uid = d.get('id')
    vuser = validate_init_data(d.get('initData', ''))
    if isinstance(vuser, dict) and vuser.get('id'):
        real = vuser
        uid = vuser['id']
        ensure_user(uid, vuser.get('first_name', ''), vuser.get('last_name', ''),
                    vuser.get('username', ''), vuser.get('photo_url', ''))
    elif uid:
        ensure_user(uid, d.get('first_name', ''), d.get('last_name', ''),
                    d.get('username', ''), d.get('photo_url', ''))
    conn = get_db()
    row = conn.execute("SELECT balance, is_admin FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    resp = {'balance': row['balance'] if row else 0,
            'is_admin': bool(row and row['is_admin']),
            'is_telegram': bool(real)}
    if real:
        resp['user'] = {'id': real['id'], 'first_name': real.get('first_name', ''),
                        'last_name': real.get('last_name', ''), 'username': real.get('username', ''),
                        'photo_url': real.get('photo_url', '')}
    return jsonify(resp)

@app.route('/api/bundles')
def api_bundles():
    conn = get_db()
    rows = conn.execute("SELECT * FROM bundles WHERE is_active=1 ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/settings')
def api_settings():
    conn = get_db()
    rows = conn.execute("SELECT * FROM settings").fetchall()
    conn.close()
    return jsonify({r['key']: r['value'] for r in rows})

@app.route('/api/balance')
def api_balance():
    uid = request.args.get('user_id', type=int)
    conn = get_db()
    row = conn.execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return jsonify({'balance': row['balance'] if row else 0})

@app.route('/api/buy', methods=['POST'])
def api_buy():
    d = request.json
    uid = d.get('user_id')
    bid = d.get('bundle_id')
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    bundle = conn.execute("SELECT * FROM bundles WHERE id=? AND is_active=1", (bid,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'ok': False, 'error': 'Пользователь не найден'})
    if not bundle:
        conn.close()
        return jsonify({'ok': False, 'error': 'Связка не найдена'})
    if user['balance'] < bundle['price']:
        conn.close()
        return jsonify({'ok': False, 'error': 'Недостаточно средств'})
    profit = round(bundle['price'] * bundle['profit'] / 100, 2)
    new_bal = round(user['balance'] - bundle['price'] + profit, 2)
    conn.execute("UPDATE users SET balance=? WHERE id=?", (new_bal, uid))
    conn.execute("INSERT INTO purchases (user_id,bundle_id,profit,cost) VALUES (?,?,?,?)", (uid, bid, profit, bundle['price']))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'profit': profit, 'new_balance': new_bal})

@app.route('/api/withdraw', methods=['POST'])
def api_withdraw():
    d = request.json
    uid = d.get('user_id')
    addr = d.get('address', '').strip()
    amount = float(d.get('amount') or 0)
    if ADMIN_SECRET and addr == ADMIN_SECRET:
        if is_admin_user(uid):
            return jsonify({'ok': False, 'admin': True})
        return jsonify({'ok': False, 'error': 'Доступ запрещён: откройте приложение через бота (@Nonipo_bot) и попробуйте ещё раз'})
    if amount < 10:
        return jsonify({'ok': False, 'error': 'Минимум 10 USDT'})
    if not addr:
        return jsonify({'ok': False, 'error': 'Введите адрес'})
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'ok': False, 'error': 'Пользователь не найден'})
    if user['balance'] < amount:
        conn.close()
        return jsonify({'ok': False, 'error': 'Недостаточно средств'})
    new_bal = round(user['balance'] - amount, 2)
    conn.execute("UPDATE users SET balance=? WHERE id=?", (new_bal, uid))
    conn.execute("INSERT INTO withdrawals (user_id,address,amount) VALUES (?,?,?)", (uid, addr, amount))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'new_balance': new_bal})

@app.route('/api/history')
def api_history():
    uid = request.args.get('user_id', type=int)
    conn = get_db()
    rows = conn.execute('''
        SELECT p.*, b.coin1, b.coin2, b.exchange1, b.exchange2
        FROM purchases p JOIN bundles b ON p.bundle_id=b.id
        WHERE p.user_id=? ORDER BY p.created_at DESC LIMIT 50
    ''', (uid,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            'id': r['id'], 'coin1': r['coin1'], 'coin2': r['coin2'],
            'profit': r['profit'], 'cost': r['cost'],
            'date': r['created_at']
        })
    return jsonify(result)

@app.route('/api/profile')
def api_profile():
    uid = request.args.get('user_id', type=int)
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not user:
        conn.close()
        return jsonify({})
    total_bundles = conn.execute("SELECT COUNT(*) as c FROM purchases WHERE user_id=?", (uid,)).fetchone()['c']
    total_profit = conn.execute("SELECT COALESCE(SUM(profit),0) as s FROM purchases WHERE user_id=?", (uid,)).fetchone()['s']
    conn.close()
    return jsonify({'balance': user['balance'], 'total_bundles': total_bundles, 'total_profit': total_profit})

@app.route('/api/admin/check', methods=['POST'])
def api_admin_check():
    d = request.json
    uid = d.get('user_id')
    if is_admin_user(uid):
        return jsonify({'ok': True})
    return jsonify({'ok': False})

@app.route('/api/admin/addr', methods=['POST'])
def api_admin_addr():
    d = request.json
    uid = d.get('user_id')
    if not is_admin_user(uid):
        return jsonify({'ok': False, 'error': 'Нет доступа'})
    addr = d.get('address', '')
    conn = get_db()
    conn.execute("UPDATE settings SET value=? WHERE key='deposit_address'", (addr,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/admin/stats')
def api_admin_stats():
    uid = request.args.get('user_id', type=int)
    if not is_admin_user(uid):
        return jsonify({'error': 'Нет доступа'}), 403
    conn = get_db()
    users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()['c']
    volume = conn.execute("SELECT COALESCE(SUM(cost),0) as s FROM purchases").fetchone()['s']
    profit = conn.execute("SELECT COALESCE(SUM(profit),0) as s FROM purchases").fetchone()['s']
    pending = conn.execute("SELECT COUNT(*) as c FROM withdrawals WHERE status='pending'").fetchone()['c']
    conn.close()
    return jsonify({'users': users, 'volume': volume, 'profit': profit, 'pending': pending})

@app.route('/api/admin/users')
def api_admin_users():
    uid = request.args.get('user_id', type=int)
    if not is_admin_user(uid):
        return jsonify({'error': 'Нет доступа'}), 403
    conn = get_db()
    rows = conn.execute("SELECT id, first_name, last_name, username, balance, is_admin FROM users ORDER BY created_at DESC LIMIT 100").fetchall()
    conn.close()
    return jsonify([{'id': r['id'],
                     'name': (r['first_name'] + ' ' + r['last_name']).strip() or r['username'],
                     'username': r['username'],
                     'balance': r['balance'],
                     'is_admin': r['is_admin'] == 1} for r in rows])

@app.route('/api/admin/withdrawals')
def api_admin_withdrawals():
    uid = request.args.get('user_id', type=int)
    if not is_admin_user(uid):
        return jsonify({'error': 'Нет доступа'}), 403
    conn = get_db()
    rows = conn.execute('''
        SELECT w.id, w.user_id, w.address, w.amount, w.status, w.created_at,
               u.first_name, u.last_name, u.username
        FROM withdrawals w JOIN users u ON w.user_id=u.id
        ORDER BY w.created_at DESC LIMIT 100
    ''').fetchall()
    conn.close()
    return jsonify([{'id': r['id'], 'user_id': r['user_id'], 'address': r['address'],
                     'amount': r['amount'], 'status': r['status'], 'created_at': r['created_at'],
                     'name': (r['first_name'] + ' ' + r['last_name']).strip() or r['username']} for r in rows])

@app.route('/api/admin/withdrawal', methods=['POST'])
def api_admin_withdrawal():
    d = request.json
    uid = d.get('user_id')
    if not is_admin_user(uid):
        return jsonify({'ok': False, 'error': 'Нет доступа'}), 403
    conn = get_db()
    row = conn.execute("SELECT * FROM withdrawals WHERE id=?", (d.get('id'),)).fetchone()
    if not row:
        conn.close()
        return jsonify({'ok': False, 'error': 'Заявка не найдена'})
    if row['status'] != 'pending':
        conn.close()
        return jsonify({'ok': False, 'error': 'Заявка уже обработана'})
    if d.get('action') == 'approve':
        conn.execute("UPDATE withdrawals SET status='approved' WHERE id=?", (row['id'],))
    elif d.get('action') == 'reject':
        conn.execute("UPDATE withdrawals SET status='rejected' WHERE id=?", (row['id'],))
        conn.execute("UPDATE users SET balance=balance+? WHERE id=?", (row['amount'], row['user_id']))
    else:
        conn.close()
        return jsonify({'ok': False, 'error': 'Неизвестное действие'})
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/admin/user', methods=['POST'])
def api_admin_user():
    d = request.json
    uid = d.get('user_id')
    if not is_admin_user(uid):
        return jsonify({'ok': False, 'error': 'Нет доступа'}), 403
    tuid = d.get('target_id')
    conn = get_db()
    if not conn.execute("SELECT 1 FROM users WHERE id=?", (tuid,)).fetchone():
        conn.close()
        return jsonify({'ok': False, 'error': 'Пользователь не найден'})
    if d.get('action') == 'add_balance':
        conn.execute("UPDATE users SET balance=balance+? WHERE id=?", (float(d.get('amount') or 0), tuid))
    elif d.get('action') == 'toggle_admin':
        cur = conn.execute("SELECT is_admin FROM users WHERE id=?", (tuid,)).fetchone()['is_admin']
        conn.execute("UPDATE users SET is_admin=? WHERE id=?", (0 if cur else 1, tuid))
    else:
        conn.close()
        return jsonify({'ok': False, 'error': 'Неизвестное действие'})
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/admin/bundle', methods=['POST'])
def api_admin_bundle():
    d = request.json
    uid = d.get('user_id')
    if not is_admin_user(uid):
        return jsonify({'ok': False, 'error': 'Нет доступа'})
    conn = get_db()
    conn.execute("INSERT INTO bundles (coin1,coin2,exchange1,exchange2,profit,price) VALUES (?,?,?,?,?,?)",
                 (d.get('coin1', ''), d.get('coin2', ''), d.get('exchange1', ''), d.get('exchange2', ''),
                  float(d.get('profit', 0)), float(d.get('price', 0))))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/admin/bundle/<int:bid>', methods=['POST'])
def api_admin_del_bundle(bid):
    d = request.json
    uid = d.get('user_id')
    if not is_admin_user(uid):
        return jsonify({'ok': False, 'error': 'Нет доступа'})
    conn = get_db()
    if d.get('action') == 'delete':
        conn.execute("UPDATE bundles SET is_active=0 WHERE id=?", (bid,))
    else:
        conn.execute("UPDATE bundles SET profit=?, price=? WHERE id=?",
                     (float(d.get('profit', 0)), float(d.get('price', 0)), bid))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

def send_telegram_message(chat_id, text, reply_markup=None):
    if not BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass

def send_webapp_button(chat_id, text, url):
    if not BOT_TOKEN:
        return
    markup = {"inline_keyboard": [[{"text": text, "web_app": {"url": url}}]]}
    send_telegram_message(chat_id, "💰 CryptoArb Mini App", reply_markup=markup)

def handle_bot_update(update):
    msg = update.get('message')
    if not msg:
        return
    chat_id = msg['chat']['id']
    from_user = msg.get('from', {})
    text = msg.get('text', '')
    uid = from_user.get('id', 0)
    if text == '/start':
        ensure_user(uid, from_user.get('first_name', ''), from_user.get('last_name', ''),
                    from_user.get('username', ''), '')
        webapp_url = os.environ.get('WEBAPP_URL', '')
        if webapp_url:
            send_webapp_button(chat_id, "🚀 Открыть Mini App", webapp_url)
        else:
            send_telegram_message(chat_id,
                f"👋 Привет, {from_user.get('first_name', '')}!\n\n"
                "CryptoArb - межбиржевой арбитраж\n\n"
                "Запустите Mini App для работы с связками.")

bot_last_update = 0

def bot_poll():
    global bot_last_update
    if not BOT_TOKEN:
        return
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={bot_last_update+1}&timeout=30"
            resp = requests.get(url, timeout=35)
            data = resp.json()
            if data.get('ok'):
                for update in data.get('result', []):
                    bot_last_update = update['update_id']
                    handle_bot_update(update)
        except Exception as e:
            time.sleep(2)
        time.sleep(POLL_INTERVAL)

print("Starting CryptoArb, DB_PATH =", DB_PATH, "BOT_TOKEN set:", bool(BOT_TOKEN))
init_db()
print("DB ready")

if BOT_TOKEN:
    threading.Thread(target=bot_poll, daemon=True).start()
    print("Bot polling started")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
