(function () {
  "use strict";
  var DATA_API = "https://cellbeat-mini-metrics.onrender.com";
  var QUEUE_KEY = "cellbeat-mini-beta:bleak:pending:v1";
  var CACHE_PREFIX = "cellbeat-mini-beta:bleak:remote:v1:";
  var CACHE_MS = 72 * 60 * 60 * 1000;
  var MAX_PENDING = 8;
  var inflight = false;
  function parse(text) { try { return JSON.parse(text); } catch (error) { return null; } }
  function get(key) { try { return parse(localStorage.getItem(key) || ""); } catch (error) { return null; } }
  function set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); return true; } catch (error) { return false; } }
  function identity() { var value = get("cellbeat-mini-beta:identity:v2"); return value && typeof value.token === "string" ? value.token : ""; }
  function idempotencyKey(songKey, vote, at) { var who = identity() || "anonymous"; return [who, songKey, vote, Math.floor(Date.parse(at) / CACHE_MS)].join(":"); }
  function request(path, options) { options=options||{}; options.headers=options.headers||{}; options.headers["Content-Type"]="application/json"; var token=identity(); if(token)options.headers["X-Cellbeat-Identity"]=token; return fetch(DATA_API+path,options).then(function(response){return response.text().then(function(text){var data=text?parse(text):{};if(!response.ok)throw new Error((data&&data.error)||("HTTP "+response.status));return data||{};});}); }
  function validEvent(value){return value&&value.songKey&&(value.vote==="up"||value.vote==="down")&&value.at&&value.idempotencyKey;}
  function queue(){var value=get(QUEUE_KEY),items;if(validEvent(value))items=[value];else if(Array.isArray(value))items=value.filter(validEvent);else items=[];return items.slice(0,MAX_PENDING);}
  function saveQueue(items){items=items.slice(0,MAX_PENDING);try{if(!items.length)localStorage.removeItem(QUEUE_KEY);else localStorage.setItem(QUEUE_KEY,JSON.stringify(items));return true;}catch(error){return false;}}
  function enqueue(event){var items=queue(),i;for(i=0;i<items.length;i+=1){if(items[i].idempotencyKey===event.idempotencyKey)return true;}if(items.length>=MAX_PENDING)return false;items.push(event);return saveQueue(items);}
  function clearPending(key){saveQueue(queue().filter(function(event){return event.idempotencyKey!==key;}));}
  function send(event){return request("/api/bleak/vote",{method:"POST",body:JSON.stringify({song_key:event.songKey,vote:event.vote,at:event.at,idempotency_key:event.idempotencyKey})}).then(function(data){clearPending(event.idempotencyKey);if(data&&data.metrics)set(CACHE_PREFIX+event.songKey,{at:Date.now(),metrics:data.metrics});return data;});}
  function flush(){if(inflight)return Promise.resolve(false);var items=queue(),event=items[0];if(!event)return Promise.resolve(false);inflight=true;return send(event).then(function(){return true;}).catch(function(){return false;}).then(function(ok){inflight=false;if(ok&&queue().length)return flush();return ok;});}
  function commit(songKey,vote,at){if(!songKey||(vote!=="up"&&vote!=="down"))return Promise.resolve(false);at=at||new Date().toISOString();var event={songKey:songKey,vote:vote,at:at,idempotencyKey:idempotencyKey(songKey,vote,at)};if(!enqueue(event))return Promise.resolve(false);return flush();}
  function metrics(songKey){var cached=get(CACHE_PREFIX+songKey);if(cached&&Date.now()-Number(cached.at||0)<CACHE_MS)return Promise.resolve(cached.metrics||null);return request("/api/bleak/song/"+encodeURIComponent(songKey),{method:"GET"}).then(function(data){var value=data.metrics||data;set(CACHE_PREFIX+songKey,{at:Date.now(),metrics:value});return value;});}
  window.CellbeatMiniBleak={commit:commit,metrics:metrics,flush:flush};window.addEventListener("online",flush);window.setTimeout(flush,250);
}());
