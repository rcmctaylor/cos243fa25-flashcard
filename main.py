from fastapi import FastAPI, Depends, Request, Form, WebSocket, WebSocketDisconnect, Response, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Annotated
from contextlib import asynccontextmanager
from sqlmodel import Session, Field, SQLModel, create_engine, select, Relationship
from fastapi.middleware.cors import CORSMiddleware
import random
from db.session import create_db_and_tables, get_session, SessionDep
from db.models import Card, UserCookie
from core.templates import templates
from routers import cards, sets
import asyncio
import time
from typing import Dict
import json
from pathlib import Path



#Database code missing
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the DB
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
#app.mount("/static", StaticFiles(directory="static"), name="static")

# Add this middleware
from starlette.middleware.base import BaseHTTPMiddleware

class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Trust Railway's proxy headers
        if "x-forwarded-proto" in request.headers:
            request.scope["scheme"] = request.headers["x-forwarded-proto"]
        if "x-forwarded-host" in request.headers:
            request.scope["server"] = (request.headers["x-forwarded-host"], None)
        return await call_next(request)

app.add_middleware(ProxyHeadersMiddleware)

app.include_router(cards.router)
app.include_router(sets.router)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, session: SessionDep):     
  cards = session.exec(select(Card)).all()
  return templates.TemplateResponse(
      request=request, name="index.html", context={"cards":cards}
  )


@app.get("/learn/")
def learn(request: Request, session:SessionDep):
    cards = session.exec(select(Card)).all()
    card = cards[random.randint(0, (len(cards)-1))]
    return templates.TemplateResponse(
      request=request, name="/learn.html", context={"card":card}
  )

##Websockets
class ConnectionManager:

    #Here we will 
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        #self.user_cookies: list[UserCookie] = []
        #self.user_cookies:Dict[int, UserCookie] = {}

    #Establish a connection, add it to the list
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    #When disconnecting, remove websockt from the list
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    #Send message to a particluar socket
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    #Brodcast Message to all sockets
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

class TriviaManager:

    current_card = None

    def __init__(self):
        self.question = "What is the capital of France?"
        self.options = ["Paris", "London", "Berlin", "Madrid"]
        self.answer = "A"
        self.guesses = {}
        self.trivia = {
            "question": self.question,
            "options": self.options,
            "answer": self.answer
        }
        
    def get_trivia(self, session:SessionDep):    
        cards = session.exec(select(Card)).all()
        self.current_card = cards[random.randint(0, (len(cards)-1))]
        return self.current_card.front
    
    async def accept_guess(self, guess, client_id):
        #self.guesses[client_id] = answer
        if self.current_card is not None:
            if guess == self.current_card.back:
                await manager.broadcast(f"Correct Answer! {client_id} correctly guessed the answer: {self.current_card.back}")
            #else:
                #await manager.broadcast(f"Wrong Answer! Client ID: {client_id}. Guess was {guess}. Answer is: {self.current_card.back}. New question coming in 5 seconds...")
       
manager = ConnectionManager()
#Todo: create a manager only when there are active connecitons
triviaManager = TriviaManager()

 
@app.get("/play/")
def play(response: Response, request: Request, session:SessionDep, user_name=Cookie(default=None)):
    
    response = templates.TemplateResponse(
        request=request, name="/play.html", context={"cards":cards, "user_name": user_name}
    )
    return response
    '''
    cards = session.exec(select(Card)).all()    
    
    user_name = ""
    print(session_id)
    for uc in manager.user_cookies:
        print("|")
        print(uc)
        print("|")
    if(session_id is not None):
        user_name = "Dave"
        #user_name = manager.user_cookies[session_id].name

    

    
    if(session_id is not None):
        print("Cookie Found: "+session_id)
    else:
        session_id = (time.time() * 1000000).__int__()
        user_cookie = UserCookie()
        user_cookie.session_id = session_id

        #manager.user_cookies.append(user_cookie)
        manager.user_cookies[session_id] = user_cookie
        response.set_cookie(
        key="session_id",
        value=session_id.__str__(),
        httponly=False,
        max_age=3600,
        samesite="lax"
    )        
    
    
'''
    
@app.post("/play/")
def enter_play(response: Response, request: Request, session:SessionDep, user_name: str = Form(...)):


    response = templates.TemplateResponse(
        request=request, name="/play.html", context={"cards":cards, "user_name":user_name}
    )

    response.set_cookie(key="user_name", value=user_name, httponly=False)

    return response
'''
@app.get("/trivia/client_list")
def get(request: Request, session:SessionDep):
    connectionlist = ""
    for connection in manager.active_connections
        connection_list += connection.client
    return {"msg": "hi"}
'''

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, session:SessionDep):
    
    await manager.connect(websocket)

    try:
        while True:
            #data = await websocket.receive_text()            
            data = await websocket.receive_json()
            message_type = data.get("type")
            if message_type == "trivia":
                
                try:
                    action = data['payload']['action']
                    if action == "nextQuestion":
                        await manager.broadcast("Triva Question!")
                        await manager.broadcast(triviaManager.get_trivia(session))
                except KeyError:
                    await manager.send_personal_message("Error: Unkown Key", websocket)
           
            elif message_type == "chat":                
                #await manager.send_personal_message(f"You wrote: {data}", websocket)
                await manager.broadcast(f"{client_id} says: {data['payload']['message']}")
                await triviaManager.accept_guess(data['payload']['message'], client_id)

    except WebSocketDisconnect:
            manager.disconnect(websocket)            
            await manager.broadcast(f"Client #{client_id} left the chat")
            
    '''
    try:
        while True:
            data = await websocket.receive_text()
            if data.startswith("/"):
                if data == "/trivia":
                    await manager.send_personal_message(f"Trivia: {triviaManager.getTrivia()['question']}", websocket)
                    await manager.send_personal_message(f"Options: {', '.join(triviaManager.getTrivia()['options'])}", websocket)
                    #await manager.send_personal_message(f"Answer: {trivia['answer']}", websocket)
                            
                elif data == "/trivia showanswer":
                    await manager.broadcast(triviaManager.showAnswer())

                elif data == "/trivia A" or data == "/trivia B" or data == "/trivia C" or data == "/trivia D":
                        triviaManager.accept_guess(data.strip("/trivia "), client_id)
                        if triviaManager.getTrivia() and data.strip("/trivia ") == triviaManager.getTrivia()['answer']:
                            await manager.send_personal_message("Correct!", websocket)
                        else:
                            await manager.send_personal_message("Incorrect!", websocket)
                elif data == "/trivia showStats":
                    await manager.broadcast(triviaManager.showStats())
            else:
                await manager.send_personal_message(f"You wrote: {data}", websocket)
                await manager.broadcast(f"Client #{client_id} says: {data}")
            
            

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
    '''
