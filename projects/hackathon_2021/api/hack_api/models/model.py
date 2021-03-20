# No explicit models used with mongo-db - just called directly
# simply defining some useful definitions here.

from .base import mongo_db

MONGO_DB = 'avatar_db'
MONGO_NODE_CLN = 'node_cln'
MONGO_LINK_CLN = 'link_cln'
MONGO_DATA_CLN = 'data_cln'

# TODO: split between test and avatar using prefix
def get_mongo_collection(cln, prefix=''):
    return mongo_db.db[cln]
