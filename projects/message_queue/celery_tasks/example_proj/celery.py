from celery import Celery

# TODO: restructure file appropriately
# TODO: what does the log look like
# TODO: what does rabbitmq do
# TODO: what does task database do


# TODO: Credentials should be somewhere else...
# Move a bunch of this stuff to config

app = Celery(
    'tasks',
    broker='amqp://{user}:{pswd}@localhost:5672/{vhost}'.format(
        user='admin',
        pswd='1234',
        vhost='example'
    ),
    backend='db+mysql+mysqlconnector://{user}:{pswd}@127.0.0.1:3306/{dbname}?auth_plugin=mysql_native_password'.format(
        user='root',
        pswd='1234',
        dbname='db_celery_example'
    ),
    include=['example_proj.tasks']
)
