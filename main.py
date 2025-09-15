from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Field, SQLModel, Relationship, select
from contextlib import asynccontextmanager
from db.session import create_db_and_tables, SessionDep

templates = Jinja2Templates(directory="templates")

#new comment for git
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
    front: str
    back: str
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
async def get_cards(q:str=""):
    search_results = []
    for card in card_list:
        if q in card.question:
            search_results.append(card)
    return search_results

#Path Parameter
@app.get("/cards/{card_id}", name="get_card", response_class=HTMLResponse)
async def get_card_by_id(card_id:int, request:Request):
    current_card = None
    for card in card_list:
        if card.id == card_id:
            current_card = card
    return templates.TemplateResponse(
        request=request, name="card.html", context={"card": current_card}
    )

#Post Request to add card
@app.post("/card/add")
async def add_card(card:Card):
    card_list.append(card)
    return card_list

@app.get("/sets", name="get_set", response_class=HTMLResponse)
async def get_sets(session: SessionDep, request:Request):
    sets = session.exec(select(Set).order_by(Set.name)).all()
    return templates.TemplateResponse(
        request=request, name="sets.html", context={"sets": sets}
    )

@app.get("/users", name="get_user", response_class=HTMLResponse)
async def get_users(request:Request):
    return templates.TemplateResponse(
        request=request, name="users.html", context={"users": user_list}
    )

@app.post("/sets/add")
async def create_set(session: SessionDep, set:Set):
    db_set = Set(name=set.name)
    session.add(db_set)
    session.commit()
    session.refresh(db_set)
    return db_set