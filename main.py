from fastapi import FastAPI, Depends, Request, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Annotated
from contextlib import asynccontextmanager
from sqlmodel import Session, Field, SQLModel, create_engine, select
import random



class Card(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    front: str
    back: str

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

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, session: SessionDep):     
  cards = session.exec(select(Card)).all()
  return templates.TemplateResponse(
      request=request, name="index.html", context={"cards":cards}
  )

@app.get("/cards/")
def get_cards(request: Request, session:SessionDep):
    cards = session.exec(select(Card)).all()
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
def edit_cards(request: Request, session:SessionDep):
    cards = session.exec(select(Card)).all()
    return templates.TemplateResponse(
      request=request, name="/cards/add.html", context={"cards":cards}
  )
    

@app.post("/cards/add")
async def submcreate_card(session: SessionDep, front: str = Form(...), back: str = Form(...)):
#def create_card(card: Card, session: SessionDep):
    #db_card = Card.model_validate(card)
    db_card = Card(front=front, back=back)
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
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    #return card
    return templates.TemplateResponse(
      request=request, name="/cards/card.html", context={"card":card, "action":action}
  )

