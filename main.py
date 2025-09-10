from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse

templates = Jinja2Templates(directory="templates")

app = FastAPI()

class Card(BaseModel):
    id:int
    question:str
    answer:str

class Set(BaseModel):
    id: int
    name: str

card_list = [
  Card(id=1, question="Where is Taylor located?", answer="Upland, IN"),
  Card(id=2, question="What is the capital of Indiana?", answer="Indianapolis, IN")
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
@app.get("/cards/{card_id}", name="get_card")
async def get_card_by_id(card_id:int):
    for card in card_list:
        if card.id == card_id:
            return card
    return None

#Post Request to add card
@app.post("/card/add")
async def add_card(card:Card):
    card_list.append(card)
    return card_list

