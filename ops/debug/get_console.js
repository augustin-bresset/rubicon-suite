const WebSocket = require('ws');
const fs = require('fs');

const url = fs.readFileSync('ws_url.txt', 'utf8').trim();
const ws = new WebSocket(url);

ws.on('open', () => {
    ws.send(JSON.stringify({id: 1, method: 'Log.enable'}));
    ws.send(JSON.stringify({id: 2, method: 'Runtime.enable'}));
    console.log("Listening for Chrome console errors...");
    setTimeout(() => { ws.close(); process.exit(); }, 6000);
});

ws.on('message', (data) => {
    const msg = JSON.parse(data);
    if (msg.method === 'Runtime.consoleAPICalled' && msg.params.type === 'error') {
        console.error("BROWSER ERROR:", msg.params.args);
    }
    if (msg.method === 'Runtime.exceptionThrown') {
        console.error("BROWSER EXCEPTION:", msg.params.exceptionDetails);
    }
});
