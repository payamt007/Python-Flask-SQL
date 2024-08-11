import json


def test_400_responses(client):
    response = client.get("/rates?date_from=2015-02-4")
    assert response.status_code == 400
    response_data = json.loads(response.get_data(as_text=True))
    assert "date_to should be determined" in response_data["errors"]
    assert "destination should be determined" in response_data["errors"]
    assert "origin should be determined" in response_data["errors"]
