from gevent import monkey
monkey.patch_all()

import stf_api

app = stf_api.create_app()

if __name__ == '__main__':
    # running from host
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://app_user:1234@localhost:5432/stf_db'
    app.run(host='0.0.0.0', port=8050, debug=True)
