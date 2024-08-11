import json


def test_normal_request(client):
    response = client.get(
        "/rates?date_from=2016-01-01&date_to=2016-01-31&origin=CNSGH&destination=north_europe_main"
    )
    assert response.status_code == 200
    response_data = json.loads(response.get_data(as_text=True))
    assert "average_price", "day" in response_data[0]


# Test with invalid origin/destination codes
def test_invalid_origin_destination(client):
    response = client.get(
        "/rates?date_from=2016-01-01&date_to=2016-01-31&origin=INVLD&destination=INVDD"
    )
    assert response.status_code == 200
    response_data = json.loads(response.get_data(as_text=True))
    # Check if the response handles the invalid codes correctly
    assert response_data == []
