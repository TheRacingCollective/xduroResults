from flask import Flask, make_response, send_from_directory, request, jsonify
import os
from load import XduroResultBuilder, to_s3

app = Flask('XDURO')

segments = [25750409, 25750487, 25750527, 25750586, 25750610]
path = 'racingCollective/duro/penn/21.json'
results_builder = XduroResultBuilder(segments, 'PennDURO')


@app.route('/segment/<segment_id>', methods=['POST'])
def post_segment(segment_id):
    segment_csv = request.data
    results_builder.store_segment_results(int(segment_id), segment_csv)
    resp = make_response()
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/uploadRequest', methods=['POST'])
def upload_request():
    results = results_builder.get_results()
    to_s3(path, results)
    resp = make_response()
    return resp


@app.route('/results')
def get_results():
    results = results_builder.get_results()
    return results


@app.route('/results/raw')
def get_raw_results():
    return jsonify(results_builder.results)


@app.route('/')
def index():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'index.html', mimetype='text/html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')
