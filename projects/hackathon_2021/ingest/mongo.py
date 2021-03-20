from pymongo import MongoClient


class Mongo(object):
    """
        Preferred Usage:
        >>> with Mongo() as m:
        >>>     m.do_stuff()
    """
    # TODO: store credentials somewhere
    # TODO: configure non-root users:
    #     - one user for updating particular database
    CONNECTION_STR = 'mongodb://{user}:{pswd}@{host}:{port}/'.format(
        user="root", pswd="1234", host="localhost", port="27017"
    )
    MONGO_DB = 'avatar_db'
    MONGO_NODE_CLN = 'node_cln'
    MONGO_LINK_CLN = 'link_cln'
    MONGO_DATA_CLN = 'data_cln'

    def __init__(self):
        self.client = None
        self.setup_client()

    def __enter__(self):
        self.setup_client()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_client()

    def setup_client(self):
        if self.client is None:
            # connect=False to make sure that connection only happens on first
            # operation this is done to ensure that the connection is created
            # on the forked process.
            self.client = MongoClient(Mongo.CONNECTION_STR, connect=False)

    def close_client(self):
        if self.client is not None:
            self.client.close()
            self.client = None

    def get_collection(self, cln_name):
        return self.client[Mongo.MONGO_DB][cln_name]
