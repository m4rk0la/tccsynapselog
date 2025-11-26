import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome' in response.data  # Adjust based on actual content

def test_about_page(client):
    response = client.get('/about')
    assert response.status_code == 200
    assert b'About Us' in response.data  # Adjust based on actual content

def test_non_existent_page(client):
    response = client.get('/non-existent')
    assert response.status_code == 404