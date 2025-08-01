from fastapi import FastAPI, Depends, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Annotated
from contextlib import asynccontextmanager
from sqlmodel import Session, Field, SQLModel, create_engine, select, Relationship
import random
from .db.session import create_db_and_tables, get_session, SessionDep
from .db.models import Card
from .core.templates import templates
from .routers import cards, sets


#Database code missing
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the DB
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(cards.router, )
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