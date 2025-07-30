from fastapi import FastAPI, Depends, Request, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Annotated
from contextlib import asynccontextmanager
from sqlmodel import Session, Field, SQLModel, create_engine, select, Relationship
import random

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

# Configure Jinja2 templates directory
templates = Jinja2Templates(directory="templates")

#SQL Code Setup
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the DB
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, session: SessionDep):     
  cards = session.exec(select(Card)).all()
  return templates.TemplateResponse(
      request=request, name="index.html", context={"cards":cards}
  )

@app.get("/cards/")
def get_cards(request: Request, session:SessionDep):
    cards = session.exec(select(Card).order_by(Card.front)).all()
    return templates.TemplateResponse(
      request=request, name="/cards/cards.html", context={"cards":cards}
  )

@app.get("/learn/")
def learn(request: Request, session:SessionDep):
    cards = session.exec(select(Card)).all()
    card = cards[random.randint(0, (len(cards)-1))]
    return templates.TemplateResponse(
      request=request, name="/learn.html", context={"card":card}
  )

@app.get("/cards/add")
def edit_cards(request: Request, session:SessionDep, set_id:int = 0):
    cards = session.exec(select(Card)).all()
    sets = session.exec(select(Set)).all()
    return templates.TemplateResponse(
      request=request, name="/cards/add.html", context={"cards":cards, "sets":sets, "set_id":set_id}
  )
    

@app.post("/cards/add")
async def create_card(session: SessionDep, front: str = Form(...), back: str = Form(...), set_id: int = Form(...)):
#def create_card(card: Card, session: SessionDep):
    #db_card = Card.model_validate(card)
    db_card = Card(front=front, back=back, set_id=set_id)    
    session.add(db_card)
    session.commit()
    session.refresh(db_card)
    #return db_card
    #return {"message": "Form submitted successfully", "user": db_card.model_dump()}
    #return templates.TemplateResponse("card.html", {"request": request, "card": card})
    return RedirectResponse(url=f"/cards/{db_card.id}", status_code=303)

@app.get("/cards/{id}")
def get_card(request: Request, session:SessionDep, id:int,action:str="view"):
    
    card = session.exec(select(Card).where(Card.id == id)).first()
    sets = session.exec(select(Set)).all()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    #return card
    return templates.TemplateResponse(
      request=request, name="/cards/card.html", context={"card":card, "action":action, "sets":sets}
  )


#Update Cards
@app.post("/cards/{card_id}/edit", response_model=Card)
def update_card(card_id: int, session: SessionDep, front: str = Form(...), back: str = Form(...), set_id: int = Form(...)):
    db_card = session.get(Card, card_id)    
    if not db_card:
        raise HTTPException(status_code=404, detail="Card not found")
    db_card.front = front
    db_card.back = back
    db_card.set_id = set_id
    card_data = db_card.model_dump(exclude_unset=True)
    db_card.sqlmodel_update(card_data)
    session.add(db_card)
    session.commit()
    session.refresh(db_card)
    #return db_card
    return RedirectResponse(url=f"/cards/{db_card.id}", status_code=303)

@app.post("/cards/{card_id}/delete")
def delete_card(card_id:int, session: SessionDep):
    db_card = session.get(Card, card_id)
    if not db_card:
        raise HTTPException(status_code=404, detail="Card not found")
    session.delete(db_card)
    session.commit()
    return RedirectResponse(url="/cards/", status_code=303)

@app.get("/sets/")
def get_sets(request: Request, session:SessionDep):
    sets = session.exec(select(Set).order_by(Set.name)).all()
    return templates.TemplateResponse(
      request=request, name="/sets/sets.html", context={"sets":sets}
  )

@app.get("/sets/{id}")
def get_set(request: Request, session:SessionDep, id:int,action:str="view"):
    
    set = session.exec(select(Set).where(Set.id == id)).first()
    #cards = session.exec(select(Card).where(Card.set_id==id)).all()
    if set is not None:
        cards = set.cards
    
    if not set:
        raise HTTPException(status_code=404, detail="Set not found")
    
    return templates.TemplateResponse(
      request=request, name="/sets/set.html", context={"set":set, "action":action, "cards":cards}
  )

@app.get("/sets/add/")
def add_sets(request: Request, session:SessionDep):
    sets = session.exec(select(Set)).all()
    return templates.TemplateResponse(
      request=request, name="/sets/add.html", context={"sets":sets}
  )
    
@app.post("/sets/add")
async def create_set(session: SessionDep, name: str = Form(...)):
#def create_card(card: Card, session: SessionDep):
    #db_card = Card.model_validate(card)
    db_set = Set(name=name)
    session.add(db_set)
    session.commit()
    session.refresh(db_set)
    return RedirectResponse(url=f"/sets/{db_set.id}", status_code=303)

#Update Cards
@app.post("/sets/{set_id}/edit", response_model=Set)
def update_set(set_id: int, session: SessionDep, name: str = Form(...)):
    db_set = session.get(Set, set_id)    
    if not db_set:
        raise HTTPException(status_code=404, detail="Card not found")
    db_set.name = name    
    card_data = db_set.model_dump(exclude_unset=True)
    db_set.sqlmodel_update(card_data)
    session.add(db_set)
    session.commit()
    session.refresh(db_set)
    #return db_card
    return RedirectResponse(url=f"/sets/{db_set.id}", status_code=303)