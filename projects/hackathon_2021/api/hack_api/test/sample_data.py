from hack_api.tasks import ingest_sample_data

def test_queue():
    ingest_sample_data.queue_task(local=True)

def test_generate():
    ingest_sample_data.generate_data(local=True)

test_generate()
