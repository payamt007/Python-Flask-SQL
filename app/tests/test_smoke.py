def test_smoke(client):
    response = client.get("/")
    assert response.status_code == 200


def test_db_smoke(client):
    response = client.get("/rates")
    assert response.status_code == 400
