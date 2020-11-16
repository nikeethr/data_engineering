import stf_api

app = stf_api.create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=True)
