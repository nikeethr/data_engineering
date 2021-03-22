from flask import Blueprint
from flask import jsonify, make_response, request, json

from hack_api.models.base import mongo_db
from hack_api.models import model
from hack_api.tasks import ingest_sample_data

# import mongo here:
# from stf_api.models.base import db

hack_bp = Blueprint('hack_api', __name__, url_prefix='/hack_api')

# --- test data routes ---

@hack_bp.route('/test/generate_test_data')
def generate_test_data():
    # TODO:
    # adds task to RQ worker queue
    ingest_sample_data.queue_task()
    return jsonify({
        'msg': 'generating test data'
    })

@hack_bp.route('/test/get_data')
def get_test_data():
    # TODO:
    # get data collection
    cln = model.get_mongo_collection(model.MONGO_DATA_CLN)
    data = list(cln.find({}, {'_id': False}))
    return jsonify(data)

@hack_bp.route('/test/get_data_groups')
def get_test_data_group():
    payload = request.get_json()
    groups = payload['groups']
    cln = model.get_mongo_collection(model.MONGO_DATA_CLN)
    data = list(cln.find(
        { 'group': { '$in': groups } }, 
        { '_id': False }
    ))
    return jsonify(data)


@hack_bp.route('/test/get_node_map')
def get_test_node_map():
    # TODO:
    # get node collection AND
    # get links collection
    node_cln = model.get_mongo_collection(model.MONGO_NODE_CLN)
    nodes = list(node_cln.find({}, {'_id': False}))
    link_cln = model.get_mongo_collection(model.MONGO_LINK_CLN)
    links = list(link_cln.find({}, {'_id': False}))
    resp = { 'nodes': nodes, 'links': links }
    return jsonify(resp)


# --- avatar app routes ---

@hack_bp.route('/analytics/insert', methods=['POST'])
def insert_entry():
    # TODO:
    # posts a document into mongodb database AND
    # adds task to RQ to recompute clusters
    pass
    
@hack_bp.route('/analytics/get_data')
def get_avatar_data():
    # TODO:
    # get data collection
    pass

@hack_bp.route('/analytics/get_node_map')
def get_avatar_node_map():
    # TODO:
    # get node collection AND
    # get links collection
    pass


