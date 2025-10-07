from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi import Request, WebSocket, WebSocketDisconnect, Cookie, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Field, SQLModel, Relationship, select
from contextlib import asynccontextmanager
from .db.session import create_db_and_tables, get_session, SessionDep

templates = Jinja2Templates(directory="templates")

#Database code missing
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the DB
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

class Set(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str    
    cards: list["Card"] = Relationship(back_populates="set")

class Card(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    question: str
    answer: str
    set_id: int | None = Field(default=None, foreign_key="set.id")
    set: Set | None = Relationship(back_populates="cards")

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str

#Let's tackle this one later because it's a many to many relationship
#This will be an advanced feature for the future
class Deck(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str    

class ConnectionManager:

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket:WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)


    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message:str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()
'''
user_list =[
    User(id=1, name="Dave", email="rcmc@taylor.edu"),
    User(id=2, name="Bob", email="bob@example.com")
]
set_list =[
    Set(id=1, name="Geography")
]
card_list = [
  Card(id=1, question="Where is Taylor located?", answer="Upland, IN", set_id=1),
  Card(id=2, question="What is the capital of Indiana?", answer="Indianapolis, IN", set_id=1)
]
'''

user_list = []
card_list = []
set_list = []


@app.get("/", response_class=HTMLResponse)
async def root(request:Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"cards": card_list}
    )

#Query parameter
@app.get("/cards")
async def get_cards(request:Request, session: SessionDep):
    cards = session.exec(select(Card).order_by(Card.question)).all()
    return templates.TemplateResponse(
        request=request, name="cards.html", context={"cards": cards}
    )

#Path Parameter
@app.get("/cards/{card_id}", name="get_card", response_class=HTMLResponse)
async def get_card_by_id(card_id:int, request:Request,session: SessionDep):
    
    card = session.exec(select(Card, card_id))

    return templates.TemplateResponse(
        request=request, name="card.html", context={"card": card}
    )

#Post Request to add card
@app.post("/card/add")
async def add_card(session: SessionDep, card:Card):
    #card_list.append(card)
    db_card = Card(question=card.question, answer=card.answer, set_id=card.set_id)
    session.add(db_card) #add card to session
    session.commit() #save Changes to database
    session.refresh(db_card) #Refresh the db_card object with the latest data from the database, like the auto-generated id
    return db_card
'''
    with session.connection() as conn:
        current_card = conn.execute(
            text("""
                INSERT INTO card (question, answer, set_id)
                 VALUES (:question, :answer, :set_id)
                 """)
        ),
        {
            "question": card.question,
            "answer": card.answer,
            "set_id": card.set_id
        }
        row = result.fetchone()
        session.commit()
'''


@app.get("/sets", name="get_set", response_class=HTMLResponse)
async def get_sets(request:Request, session: SessionDep):
    sets = session.exec(select(Set).order_by(Set.name)).all()
    return templates.TemplateResponse(
        request=request, name="sets.html", context={"sets": sets}
    )

@app.post("/sets/add")
async def add_set(session: SessionDep, name:str):
    #card_list.append(card)
    db_set = Set(name=name)
    session.add(db_set) #add card to session
    session.commit() #save Changes to database
    session.refresh(db_set) #Refresh the db_card object with the latest data from the database, like the auto-generated id
    return db_set

@app.get("/users", name="get_user", response_class=HTMLResponse)
async def get_users(request:Request):
    return templates.TemplateResponse(
        request=request, name="users.html", context={"users": user_list}
    )

@app.get("/playwithfriends")
async def play_game(request:Request, session:SessionDep, response_class=HTMLResponse):

    return templates.TemplateResponse(
        request=request, name="playwithfriends.html"
    )

@app.post("/playwithfriends")
async def enter_play(request:Request, session:SessionDep, response_class=HTMLResponse, user_name: str= Form(...)):


    response =  templates.TemplateResponse(
        request=request, name="playwithfriends.html", context={"user_name":user_name}
    )

    response.set_cookie(key="user_name",value=user_name, httponly=False)
    return response

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id:str, session:SessionDep):
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(f"{client_id} says: {data['payload']['message']}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcoast(f"Client #{client_id} left the chat")