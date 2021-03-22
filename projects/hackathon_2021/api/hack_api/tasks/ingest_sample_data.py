import numpy as np
import pandas as pd
import itertools
from scipy.cluster.hierarchy import (
    linkage, cut_tree, dendrogram, to_tree, leaders
)
import json
from rq import Queue, Connection
from rq.job import Job
from redis import Redis

from .mongo import Mongo


def mock_data():
    N = 1000

    # --- rating ---
    # uniform distribution uneven sampling
    # 1 = 0.05
    # 2 = 0.1
    # 3 = 0.3
    # 4 = 0.4
    # 5 = 0.15
    # average = 3.9
    tmp = np.random.uniform(low=0.0, high=1.0, size=N)
    ratings = np.empty(N, dtype=np.int)
    ratings[tmp < 0.05] = 1
    ratings[(tmp >= 0.05) & (tmp < 0.15)] = 2
    ratings[(tmp >= 0.15) & (tmp < 0.45)] = 3
    ratings[(tmp >= 0.45) & (tmp < 0.85)] = 4
    ratings[(tmp >= 0.85) & (tmp <= 1.0)] = 5
    
    # --- weather ---
    # TODO: dumb numbers for now
    # temperature = -2 -> 42
    # rain_pct = 0 -> 100
    # uv = 0 -> 14
    temperature = np.random.normal(loc=22, scale=10, size=N)
    rain_pct = (np.digitize(
        np.random.beta(a=1, b=3, size=N) * 100,
        bins=np.arange(0, 101, 10)
    ) - 1) * 10
    uv = (np.digitize(
        np.random.beta(a=3, b=2, size=N) * 14,
        bins=np.arange(1, 15, 1)
    )) + 1

    # --- thresholds ---
    # invent for now + rng
    # + rng
    
    # --- icon set ---
    # invent thresholds for now
    # scarf_1
    # glasses_1
    avatar_parts = [
        'scarf',
        'sunnies',
        'hat',
        'beanie',
        'hoodie',
        'jacket',
        'sunscreen',
        'umbrella'
    ]
    num_parts = np.random.randint(low=1, high=len(avatar_parts), size=N)
    p_rel_1 = np.array([0.3, 0.2, 0.2, 0.05, 0.1, 0.6, 0.2, 0.1])
    p_rel_1 = p_rel_1 / np.sum(p_rel_1)
    p_rel_2 = np.array([0.3, 0.7, 0.5, 0.2, 0.5, 0.1, 0.2, 0.4])
    p_rel_2 = p_rel_2 / np.sum(p_rel_2)
    choice_func = lambda x: ','.join(list(
        np.random.choice(
            avatar_parts,
            size=x,
            replace=False,
            p=p_rel_1 if np.random.randint(0, 1) == 1 else p_rel_2
        )
    ))
    v_choice_func = np.vectorize(choice_func)
    avatar_set = v_choice_func(num_parts)

    df = pd.DataFrame({
        'avatar_set': avatar_set,
        'temperature': temperature,
        'rain_pct': rain_pct,
        'uv': uv,
        'rating': ratings
    })
    df['avatar_set'] = df['avatar_set'].str.split(',')

    return df


def construct_node_dict(ids, classes, tree, df):
    node_dict = {}
    links = []

    def search_tree(node, parent_ids=None):
        if node.id in ids:
            node_dict[node.id] = {
                'id': node.id,
                'groups': classes[ids == node.id].tolist(),
                'count': node.get_count(),
                'is_leaf': True
            }

            if parent_ids is not None:
                for i in parent_ids:
                    if i in node_dict:
                        node_dict[i]['groups'].extend(classes[ids == node.id].tolist())
                    else:
                        node_dict[i] = {
                            'id': i,
                            'groups': classes[ids == node.id].tolist()
                        }
        else:
            if parent_ids == None:
                parent_ids = [node.id]
            else:
                parent_ids.append(node.id)

            # append links
            links.append({ 'source': node.id, 'target': node.left.id, 'value': node.left.get_count() })
            links.append({ 'source': node.id, 'target': node.right.id, 'value': node.right.get_count() })

            # search remaining tree for nodes
            search_tree(node.left, parent_ids.copy())
            search_tree(node.right, parent_ids.copy())

    search_tree(tree)

    # fill counts for parent nodes
    for i in node_dict:
        if 'count' not in node_dict[i]:
            node_dict[i]['count'] = sum([
                node_dict[np.asscalar(ids[classes == j])]['count']
                for j in node_dict[i]['groups']
            ])
    
    # get weather averages
    for i in node_dict:
        sel = df['group'].isin(node_dict[i]['groups'])
        df_node = df.loc[sel, :]

        for j in ['temperature', 'rain_pct', 'uv', 'rating']:
            node_dict[i][j] = np.mean(df_node[j])

        avatar_sets = list(itertools.chain(
            *df_node['avatar_set'].values.tolist()
        ))

        key, count = np.unique(avatar_sets, return_counts=True)
        node_dict[i]['avatar_count'] = dict(zip(key, count.tolist()))

    return node_dict, links


def cluster_dataset(df):
    # cluster the dataset using hclust
    # get the resultant tree structure after cutting at a particular depth
    # label each tree point based on average temp/rain/uv
    N_CLUSTERS = 20
    weather_dims = ['rain_pct', 'uv', 'temperature']
    z = linkage(df[weather_dims], 'ward')
    classification = np.int32(np.squeeze(cut_tree(z, N_CLUSTERS)))
    df['group'] = classification
    # dn = dendrogram(z, p=20, truncate_mode='level', get_leaves=True)

    ids, classes = leaders(z, classification)
    rootnode = to_tree(z)
    node_dict, links = construct_node_dict(ids, classes, rootnode, df)

    return node_dict, links

def ingest_to_mongodb(df, node_dict, links, local=False):
    """
        grabs dataframe and puts elements in mongodb.
    """
    with Mongo(local) as m:
        data_cln = m.get_collection(Mongo.MONGO_DATA_CLN)
        node_cln = m.get_collection(Mongo.MONGO_NODE_CLN)
        link_cln = m.get_collection(Mongo.MONGO_LINK_CLN)

        # clear data first
        for cln in [data_cln, node_cln, link_cln]:
            cln.remove({})

        # then add the new data
        data_cln.insert_many(df.to_dict('records'))
        node_cln.insert_many(node_dict.values())
        link_cln.insert_many(links)


def queue_task(local=False):
    redis_host = 'redis'
    if local:
        redis_host = 'localhost'

    with Connection(Redis(redis_host, 6379)):
        q = Queue('hack_test_data')
        job = q.enqueue(generate_data, kwargs={ 'local': local })

    return job.id


def fetch_job_status(job_id, local=False):
    redis_host = 'redis'
    if local:
        redis_host = 'localhost'

    with Connection(Redis(redis_host, 6379)):
        job = Job.fetch(job_id)
        return job.get_status()


def generate_data(local=False):
    print(f'LOCAL_MODE: {local}')
    print('creating mock data...')
    df = mock_data()
    print('clustering dataset...')
    node_dict, links = cluster_dataset(df)
    print('ingesting to mongo db...')
    ingest_to_mongodb(df, node_dict, links, local=local)
    print('...done!')


if __name__ == '__main__':
    queue_task(local=True)
    
