from fastapi.testclient import TestClient
from sqlmodel import Session, Field, SQLModel, create_engine, select, Relationship
import re
from ..main import app, get_session
from bs4 import BeautifulSoup

#client = TestClient(app)

#Test SQL Database
'''
sqlite_file_name = "test.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)
'''

'''
def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert "Flashcard" in response.content.decode()

def test_read_item():
    response = client.get("/cards/6?action=view")
    assert response.status_code == 200
    assert "How old am i?" in response.content.decode()
'''

def test_create_set():
    engine = create_engine(  
        "sqlite:///test.db", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)  

    with Session(engine) as session:  
        def get_session_override():
            return session  
        app.dependency_overrides[get_session] = get_session_override  

    client = TestClient(app)
    
    response = client.post(
        "/sets/add", data={"name":"Science"}
    )
    
    print(response.text)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    html = response.text
    # Check if form tag exists
    assert "Science" in html
    
    #Access newly created set on its page by id
    match = re.search(r"/sets/(\d+)", html)
    assert match is not None
    item_id = match.group(1)
    print("|"+item_id)
    response = client.get("/sets/"+item_id)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text
    assert "Science" in html

    #BEAUTIFUL SOUP Test
    soup = BeautifulSoup(html, 'html.parser')
    headers = soup.find_all('h1')
    assert headers[1].text == "Science"
    

    #Newly Created set shows up on the set page
    response = client.get("/sets/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text
    assert "Science" in html    
    app.dependency_overrides.clear()