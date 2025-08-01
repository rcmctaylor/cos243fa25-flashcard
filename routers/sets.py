from fastapi import APIRouter, Depends, Request, Form, HTTPException
from sqlmodel import select
from ..db.session import get_session, SessionDep
from ..db.models import Card, Set
from ..core.templates import templates
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(prefix="/sets")

@router.get("/")
def get_sets(request: Request, session:SessionDep):
    sets = session.exec(select(Set).order_by(Set.name)).all()
    return templates.TemplateResponse(
      request=request, name="/sets/sets.html", context={"sets":sets}
  )

@router.get("/{id}")
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

@router.get("/add/")
def add_sets(request: Request, session:SessionDep):
    sets = session.exec(select(Set)).all()
    return templates.TemplateResponse(
      request=request, name="/sets/add.html", context={"sets":sets}
  )
    
@router.post("/add")
async def create_set(session: SessionDep, name: str = Form(...)):
    db_set = Set(name=name)
    session.add(db_set)
    session.commit()
    session.refresh(db_set)
    return RedirectResponse(url=f"/sets/{db_set.id}", status_code=303)

#Update Cards
@router.post("/{set_id}/edit", response_model=Set)
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