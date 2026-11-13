from fastapi.testclient import TestClient
from app.main import app


def test_homepage_served():
    response = TestClient(app).get('/')
    assert response.status_code == 200
    assert 'MethodMind' in response.text
    assert 'learning-form' in response.text


def test_frontend_assets_served():
    client = TestClient(app)
    assert client.get('/static/style.css').status_code == 200
    assert client.get('/static/app.js').status_code == 200
