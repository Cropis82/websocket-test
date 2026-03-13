from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from tinydb import TinyDB

app = FastAPI()
db = TinyDB('chat_db.json') # Il file del database verrà creato in automatico

# Gestore delle connessioni WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Invia lo storico dei messaggi appena un utente si connette
    history = db.all()
    for item in history:
        await websocket.send_text(item['text'])
        
    try:
        while True:
            # Ricevi il messaggio dal client
            data = await websocket.receive_text()
            
            # Salva il messaggio su TinyDB
            db.insert({'text': data})
            
            # Invia il messaggio a tutti gli utenti connessi
            await manager.broadcast(data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)