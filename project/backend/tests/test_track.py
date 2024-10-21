from fastapi import status


def track_create_and_next(client):
    res = client.post("/track/create")
    assert res.json().get("track_id") is not None

    _track_id = 1
    track_data = {
        "name": "string",
        "icon": "string",
        "water": 0,
        "coffee": 0,
        "alcohol": 0,
        "duration": 13,
        "cheating_cnt": 1,
        "delete": False,
        "alone": True,
        "calorie": 0,
        "start_date": "2024-10-12",
        "end_date": "2024-10-12"
    }
    response = client.patch(f"/track/create/next/{_track_id}", json=track_data)
    return response.json().get("id")


def test_create_track(client):
    # 트랙을 생성하는 테스트
    response = client.post("/track/create")
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("track_id") is not None


def test_create_next_track(client):
    res = client.post("/track/create")
    assert res.json().get("track_id") is not None

    _track_id = 1
    track_data = {
        "name": "string",
        "icon": "string",
        "water": 0,
        "coffee": 0,
        "alcohol": 0,
        "duration": 13,
        "cheating_cnt": 1,
        "delete": False,
        "alone": True,
        "calorie": 0,
        "start_date": "2024-10-12",
        "end_date": "2024-10-12"
    }
    response = client.patch(f"/track/create/next/{_track_id}", json=track_data)

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("id") is not None


def test_delete_track(client):
    # 특정 트랙을 삭제하는 테스트
    track_id = track_create_and_next(client)
    assert track_id is not None

    response = client.delete(f"/track/delete/{track_id}", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_update_track(client):
    track_id = track_create_and_next(client)
    assert track_id is not None
    track_data = {
      "name": "updated",
      "icon": "updated",
      "water": 0,
      "coffee": 0,
      "alcohol": 0,
      "duration": 0,
      "cheating_cnt": 2,
      "delete": False,
      "alone": True,
      "calorie": 0,
      "start_date": "2024-10-20",
      "end_date": "2024-10-20"
    }

    response = client.patch(f"/track/update/{track_id}", json=track_data, headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == status.HTTP_204_NO_CONTENT
    # assert response.json().get("name") == "updated"


def test_share_track(client):
    track_id = track_create_and_next(client)
    assert track_id is not None

    response = client.post(f"/track/share/{track_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_search_track(client):
    track_id = track_create_and_next(client)
    assert track_id is not None

    track_name = "str"
    response = client.get(f"/track/search/{track_name}?page=0&size=10")
    assert response.status_code == status.HTTP_200_OK
    assert "total" in response.json()
    assert "tracks" in response.json()


def test_get_track_info(client):
    track_id = track_create_and_next(client)
    assert track_id is not None

    response = client.get(f"/track/get/{track_id}/Info")
    assert response.status_code == status.HTTP_200_OK
    # assert response.json().get("track_name") is not None


