from hack_api.tasks import ingest_sample_data

def test():
    ingest_sample_data.queue_task(local=True)

test()
