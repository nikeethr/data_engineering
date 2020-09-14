import os
import requests
from flask import Blueprint, request, jsonify, abort, make_response
from . import nav_config


image_api = Blueprint('image_api', __name__)


@image_api.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404


# http://192.168.56.101:8051/api/v1/get_product_image?product_id=atmos_q5&variable=pr&domain=australia&forecast_period=w0&value=emn&fc_date=20200907
@image_api.route('/api/v1/get_product_image', methods=['GET'])
def get_image():
    request_args = {
        'product_id',
        'variable',
        'domain',
        'forecast_period',
        'value',
        'fc_date'
    }
    arg_dict = {}

    for arg_key in request_args:
        arg_val = request.args.get(arg_key, None)
        if arg_val is None:
            abort(404, description="resource not found.")
        arg_dict[arg_key] = arg_val

    try:
        # TODO: implement proper auth
        AUTH = (os.environ['POAMA_USER'], os.environ['POAMA_PASSWD'])

        img_path = nav_config.get_image_path(**arg_dict)
        r_img = requests.get(
            img_path, auth=AUTH, allow_redirects=True, stream=True
        )
        if not r_img.ok:
            raise ValueError
    except (KeyError, ValueError, TypeError):
        abort(404, description="Could not fetch image - invalid args.")

    # TODO: This needs to be set in the dash app rather than here which will be
    # telling the client when to revalidate.
    response = make_response(r_img.raw.read())
    response.headers.set('Content-Type', 'image/png')
    # private => try to use only browser cache
    # max-age => seconds before revalidation required
    response.headers.set('Cache-Control', 'private,max-age=86400')

    # for debugging:
    # return jsonify({
    #     'img_path': img_path,
    #     **arg_dict
    # })

    return response

