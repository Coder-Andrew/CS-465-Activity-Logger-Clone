import pytest
from app import app, ActivityLog, fix_mongo_id
from flask import json, url_for
import datetime
from time import sleep

@pytest.fixture()
def client():
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SERVER_NAME"] = "test.local"
    client = app.test_client()

    ActivityLog.drop_collection()

    # Pushing the app context allows us to make calls to the app like url_for
    # as if we were the running Flask app. Makes testing routes more resilient.
    ctx = app.app_context()
    ctx.push()

    yield client

    ctx.pop()


def populate_database_with_junk_data_for_testing(num_entries=15):
    for id in range(num_entries):
        timestamp = datetime.datetime.utcnow() + datetime.timedelta(minutes=id)
        activity = ActivityLog(
            user_id=id,
            username=f'John{id}',
            details=f'test string {id}',
            timestamp=timestamp,
        )
        activity.save()


def test_correct_data_sent_thru_POST_returns_correct_output(client):
    url = url_for("add_activity")
    data = {"username":"john","user_id":1,"details":"test"}

    response = client.post(url, data=json.dumps(data), headers={"Content-Type":"application/json"})
    assert response.status_code == 201
    d = json.loads(response.data)
    assert 'id' in d
    assert 'location' in d
    assert 'timestamp' in d
    assert d['username'] == 'john'
    assert d['user_id'] == 1
    assert d['details'] == 'test'


def test_POST_method_returns_correct_response_code_for_data_including_id_data(client):
    url = url_for("add_activity")
    data = {"username":"john","user_id":"1","details":"test", "id":"50"}

    response = client.post(url, data=json.dumps(data), headers={"Content-Type":"application/json"})
    assert response.status_code == 400


def test_POST_method_returns_correct_response_code_for_data_including_location_data(client):
    url = url_for("add_activity")
    data = {"username":"john","user_id":"1","details":"test", "location":"api/activities/1"}

    response = client.post(url, data=json.dumps(data), headers={"Content-Type":"application/json"})
    assert response.status_code == 400


def test_POST_method_returns_correct_response_code_for_data_excluding_user_id_data(client):
    url = url_for("add_activity")
    data = {"username":"john","details":"test"}

    response = client.post(url, data=json.dumps(data), headers={"Content-Type":"application/json"})
    assert response.status_code == 400


def test_POST_method_returns_correct_response_code_for_data_excluding_details_data(client):
    url = url_for("add_activity")
    data = {"username":"john","user_id":"1"}

    response = client.post(url, data=json.dumps(data), headers={"Content-Type":"application/json"})
    assert response.status_code == 400


def test_POST_method_returns_correct_response_code_for_data_excluding_username_data(client):
    url = url_for("add_activity")
    data = {"details":"test","user_id":"1"}

    response = client.post(url, data=json.dumps(data), headers={"Content-Type":"application/json"})
    assert response.status_code == 400


def test_POST_method_returns_correct_response_code_for_data_including_excess_data(client):
    url = url_for("add_activity")
    data = {"username":"john","user_id":"1","details":"test","Useless data that shouldn't be included":"wow please delete"}

    response = client.post(url, data=json.dumps(data), headers={"Content-Type":"application/json"})
    assert response.status_code == 400


def test_POST_method_returns_correct_response_code_for_data_including_excess_data_when_timestamp_is_provided(client):
    url = url_for("add_activity")
    data = {"username":"john","user_id":"1","details":"test","timestamp":datetime.datetime.utcnow(),"Useless data that shouldn't be included":"wow please delete"}

    response = client.post(url, data=json.dumps(data), headers={"Content-Type":"application/json"})
    assert response.status_code == 400


def test_POST_method_returns_correct_response_code_for_data_not_in_json_format(client):
    url = url_for("add_activity")
    data = [5,2,3]

    response = client.post(url, data=json.dumps(data), headers={"Content-Type":"application/json"})
    assert response.status_code == 400


def test_get_activities_method_returns_10_latest_entries(client):
    populate_database_with_junk_data_for_testing(15)

    response = client.get('/api/activities')
    assert response.status_code == 200
    pylist = response.get_json()['activities']

    assert len(pylist) == 10

    id = 14
    for user in pylist:
        assert user['username'] == f'John{id}'
        assert user['user_id'] == id
        assert user['details'] == f'test string {id}'
        assert isinstance(user['timestamp'],str)
        assert isinstance(user['id'],str)
        assert isinstance(user['location'],str)
        id -= 1


def test_get_specific_activity_returns_error_when_user_provides_invalid_id(client):
    populate_database_with_junk_data_for_testing(15)

    response = client.get('/api/activity/this_is_an_invalid_object_id_what_are_the_odds_that_it_was_valid')
    assert response.status_code == 404


def test_get_specific_activity_with_valid_id_returns_correct_activity(client):
    populate_database_with_junk_data_for_testing()

    first_entry = fix_mongo_id(ActivityLog.objects.first())
    
    response = client.get(url_for("get_specific_activity",activity_id=first_entry['id']))

    assert response.status_code == 200
    pydict_response = response.get_json()

    assert pydict_response['id'] == first_entry['id']
    assert pydict_response['username'] == first_entry['username']
    assert pydict_response['user_id'] == first_entry['user_id']
    assert pydict_response['details'] == first_entry['details']