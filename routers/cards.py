from fastapi import APIRouter, Depends, Request, Form, HTTPException
from sqlmodel import select
from ..db.session import get_session, SessionDep
from ..db.models import Card, Set
from ..core.templates import templates
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(prefix="/cards")

@router.get("/")
def get_cards(request: Request, session:SessionDep):
    cards = session.exec(select(Card).order_by(Card.front)).all()
    return templates.TemplateResponse(
      request=request, name="/cards/cards.html", context={"cards":cards}
  )

@router.get("/add")
def edit_cards(request: Request, session:SessionDep, set_id:int = 0):
    cards = session.exec(select(Card)).all()
    sets = session.exec(select(Set)).all()
    return templates.TemplateResponse(
      request=request, name="/cards/add.html", context={"cards":cards, "sets":sets, "set_id":set_id}
  )
    
@router.post("/add")
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

@router.get("/{id}")
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
@router.post("/{card_id}/edit", response_model=Card)
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

@router.post("/{card_id}/delete")
def delete_card(card_id:int, session: SessionDep):
    db_card = session.get(Card, card_id)
    if not db_card:
        raise HTTPException(status_code=404, detail="Card not found")
    session.delete(db_card)
    session.commit()
    return RedirectResponse(url="/cards/", status_code=303)