(function(){
"use strict";
var panel=document.getElementById("bleakFeedback"),up=document.getElementById("bleakUp"),down=document.getElementById("bleakDown"),selected=null,active=false;
var PROMPT="cellbeat-mini-beta:bleak:last-prompt:v1",INTERVAL=72*60*60*1000;
function due(){try{var t=Number(localStorage.getItem(PROMPT)||0);return !t||Date.now()-t>=INTERVAL;}catch(e){return true;}}
function mark(){try{localStorage.setItem(PROMPT,String(Date.now()));}catch(e){}}
function render(){if(up)up.setAttribute("aria-pressed",selected==="up"?"true":"false");if(down)down.setAttribute("aria-pressed",selected==="down"?"true":"false");}
function show(){if(active||!due()||!panel)return;mark();selected=null;active=true;render();panel.hidden=false;}
function hide(){active=false;selected=null;render();if(panel)panel.hidden=true;}
function capture(){var blob=null,old=URL.createObjectURL,click=HTMLAnchorElement.prototype.click,button=document.getElementById("savePatternBtn");if(!button)return Promise.reject();URL.createObjectURL=function(b){blob=b;return old.call(URL,b);};HTMLAnchorElement.prototype.click=function(){};try{button.click();}finally{URL.createObjectURL=old;HTMLAnchorElement.prototype.click=click;}return blob?blob.text():Promise.reject();}
function normalize(text){try{var d=JSON.parse(text),w=d.world||d;if(w){w=JSON.parse(JSON.stringify(w));w.step=0;if(w.home)w.robot=JSON.parse(JSON.stringify(w.home));if("robotCounter" in w)w.robotCounter=0;if(Array.isArray(w.mutedRobots))w.mutedRobots=[];if(Array.isArray(w.companions))w.companions.forEach(function(b){if(b.home)b.pose=JSON.parse(JSON.stringify(b.home));if("counter" in b)b.counter=0;});if(Array.isArray(w.grids))w.grids.forEach(function(g){if(Array.isArray(g.cells))g.cells.forEach(function(c){if(c&&typeof c==="object"&&"count" in c)c.count=0;});});if(d.world)d.world=w;else d=w;}return JSON.stringify(d);}catch(e){return text;}}
function hash(text){if(crypto&&crypto.subtle&&window.TextEncoder)return crypto.subtle.digest("SHA-256",new TextEncoder().encode(text)).then(function(buf){return Array.prototype.map.call(new Uint8Array(buf),function(b){return b.toString(16).padStart(2,"0");}).join("");});var h=2166136261;for(var i=0;i<text.length;i++){h^=text.charCodeAt(i);h=Math.imul(h,16777619);}return Promise.resolve("fnv1a-"+(h>>>0).toString(16)+"-"+text.length);}
function commit(){if(!active)return;var vote=selected;hide();if(!vote||!window.CellbeatMiniBleak)return;capture().then(normalize).then(hash).then(function(key){return window.CellbeatMiniBleak.commit(key,vote,new Date().toISOString());}).catch(function(){});}
if(up)up.addEventListener("click",function(){if(active){selected="up";render();}});if(down)down.addEventListener("click",function(){if(active){selected="down";render();}});
function bind(){var b=document.getElementById("playBtn");if(!b||b.dataset.betaPromptBound)return;b.dataset.betaPromptBound="1";b.addEventListener("click",function(){var stopping=b.getAttribute("aria-label")==="Stop playback"||/Stop/.test(b.textContent||"");if(stopping)commit();else setTimeout(show,100);},true);}
function randomStart(){var tries=0;function run(){var dialog=document.getElementById("randomSeedDialog"),buttons=dialog&&dialog.querySelectorAll(".seed-btn");if(!dialog||!buttons||!buttons.length){if(tries++<30)setTimeout(run,100);return;}var i=Math.floor(Math.random()*buttons.length);buttons[i].click();var yes=dialog.querySelector(".seed-yes");if(yes)yes.click();}run();}
window.addEventListener("load",function(){bind();randomStart();});setInterval(bind,1200);
}());
