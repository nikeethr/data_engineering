from gevent import monkey
monkey.patch_all()

import hack_api


app = hack_api.create_app()

if __name__ == '__main__':
    # running from localhost rather than container
    app = hack_api.create_app(local=True)
    app.run(host='0.0.0.0', port=8052)

