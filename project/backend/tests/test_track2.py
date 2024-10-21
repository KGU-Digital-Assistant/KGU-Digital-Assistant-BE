# import pytest
# from fastapi.testclient import TestClient
# from main import app
# from unittest.mock import patch
#
# client = TestClient(app)
#
#
# # Mocked current user
# class MockUser:
#     def __init__(self, id):
#         self.id = id
#
#
# # Mock the get_current_user dependency
# @pytest.fixture(autouse=True)
# def mock_get_current_user():
#     with patch("dependencies.get_current_user", return_value=MockUser(id=1)):
#         yield
#
#
# def test_get_tracks_by_name_levenshtein():
#     response = client.get("/track/search/lev/sample_track_name")
#     assert response.status_code == 200
#     assert "total" in response.json()
#     assert "tracks" in response.json()
#
#
# def test_get_my_tracks():
#     response = client.get("/track/get/mytracks")
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)
#     for track in response.json():
#         assert "id" in track
#         assert "icon" in track
#         assert "daily_calorie" in track
#         assert "name" in track
#
#
# def test_get_share_tracks():
#     response = client.get("/track/get/sharetracks")
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)
#     for track in response.json():
#         assert "id" in track
#         assert "icon" in track
#         assert "daily_calorie" in track
#         assert "name" in track
#         assert "recevied_user_id" in track
#         assert "recevied_user_name" in track
#
#
# def test_get_all_tracks():
#     response = client.get("/track/get/alltracks")
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)
#     for track in response.json():
#         assert "id" in track
#         assert "icon" in track
#         assert "daily_calorie" in track
#         assert "name" in track
#         assert "recevied_user_id" in track
#         assert "recevied_user_name" in track
