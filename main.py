from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

templates = Jinja2Templates(directory="templates")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

class Card(BaseModel):
    id:int
    question:str
    answer:str
    attempts: int = 0
    successful: int = 0
    set_id: int

class Set(BaseModel):
    id: int
    name: str

class User(BaseModel):
    id: int
    name: str
    email: str

class Deck(BaseModel):
    id:int


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
async def get_sets(request:Request):
    return templates.TemplateResponse(
        request=request, name="sets.html", context={"sets": set_list}
    )

@app.get("/users", name="get_user", response_class=HTMLResponse)
async def get_users(request:Request):
    return templates.TemplateResponse(
        request=request, name="users.html", context={"users": user_list}
    )