import time


# Test when cache is used
def test_cache_hit(client):
    # First request to store result in cache
    response1 = client.get(
        "/rates?date_from=2016-01-01&date_to=2016-01-31&origin=CNSGH&destination=north_europe_main"
    )
    assert response1.status_code == 200

    # Second request to check if it uses the cache
    response2 = client.get(
        "/rates?date_from=2016-01-01&date_to=2016-01-31&origin=CNSGH&destination=north_europe_main"
    )
    assert response2.status_code == 200

    assert response1.get_data(as_text=True) == response2.get_data(as_text=True)
    # We expect this to be the same since the second request should have used the cached result


# Test cache expiration
def test_cache_expiry(client):
    # First request to store result in cache
    response1 = client.get(
        "/rates?date_from=2016-01-01&date_to=2016-01-31&origin=CNSGH&destination=north_europe_main"
    )
    assert response1.status_code == 200

    # Wait for cache to expire (10 seconds in this case)
    time.sleep(11)

    # Second request to check if the cache has expired
    response2 = client.get(
        "/rates?date_from=2016-01-01&date_to=2016-01-31&origin=CNSGH&destination=north_europe_main"
    )
    assert response2.status_code == 200

    # We expect this to be result be same after expiration of the cache
    assert response1.get_data(as_text=True) == response2.get_data(as_text=True)
