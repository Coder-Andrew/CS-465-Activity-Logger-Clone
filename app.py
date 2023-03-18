from flask import Flask, abort, request, url_for, jsonify
from datetime import datetime
import os
from mongoengine import DateTimeField, Document, IntField, StringField, connect
from dotenv import load_dotenv
import time

load_dotenv(override=True)

#load environment variables neccessary for connecting to mongodb
mongo_host = os.getenv("DB_HOST")
mongo_db = os.getenv("DB")
mongo_user = os.getenv("DB_USER")
mongo_password = os.getenv("DB_PASSWORD")
sleep_time = float(os.getenv("SLEEP_TIME", default=0))
num_activities_to_return = int(os.getenv("N_ACTIVITIES",default=10))


#connect to mongodb using specified env variables
connect(
    db=mongo_db,
    host=mongo_host,
    username=mongo_user,
    password=mongo_password,
    retryWrites=False,
)


def fix_mongo_id(mongo_object):
    #save mongo response and return back to user
    mongo_response = mongo_object.to_mongo().to_dict()
    
    #adding activity id and location to response
    new_id = str(mongo_response['_id'])
    mongo_response['id'] = new_id
    mongo_response['location'] = url_for('get_specific_activity', activity_id=new_id)
    mongo_response.pop('_id')

    return mongo_response


#define a schema for activities to be read/written from/to mongodb
class ActivityLog(Document):
    #user_id = StringField(required = True)
    user_id = IntField(required = True)
    username = StringField(required = True)
    details = StringField(required = True)
    timestamp = DateTimeField(default=datetime.utcnow())


app = Flask(__name__)


@app.route('/api/activities', methods=['GET'])
def get_activity_log():
    query = ActivityLog.objects.order_by('-timestamp').limit(num_activities_to_return)
    activities = [fix_mongo_id(entry) for entry in query]
    return {'activities':activities}


@app.route('/api/activities/<string:activity_id>', methods=['GET'])
def get_specific_activity(activity_id):
    return_activity = ActivityLog.objects.get(id=activity_id)
    if return_activity is None:
        abort(404)
    return fix_mongo_id(return_activity),200


@app.route('/api/activities', methods=['POST'])
def add_activity(): 
    if not request.json:
        abort(400)
    new_activity = request.get_json()

    #Validate input - check to see that id and location aren't provided and received message has required elements.
    #make sure request doesn't contain data that should be handled serverside
    if ('id' in new_activity) or ('location' in new_activity):
        abort(400)

    #make sure request contains data that should be in request
    if ('user_id' not in new_activity) or ('username' not in new_activity) or ('details' not in new_activity):
        abort(400)

    #make sure request doesn't contain more data than what is required
    #change comparison number if more data is required in the future
    if ('timestamp' in new_activity) and (len(new_activity.keys()) > 4):
        abort(400)
    elif len(new_activity.keys()) > 3:
        abort(400)

    #instanstiate new Activity object and fill with json fields provided in the request
    activity = ActivityLog(
        user_id=new_activity.get('user_id'),
        username=new_activity.get('username'),
        details=new_activity.get('details'),
        timestamp=new_activity.get('timestamp'),
    )

    #save to mongodb
    activity.save()

    #simulate latency in response
    time.sleep(sleep_time)

    return fix_mongo_id(activity),201
