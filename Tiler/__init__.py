import os, base64, sqlite3, json
import uritemplate
from flask import Flask, Response, render_template, url_for
from .tippecanoe import Config, get_claypigeon_metadata, get_url_tile

slippymaps_url_template = 'http://s3.amazonaws.com/data.openaddresses.io/runs/{run_id}/slippymap.mbtiles'

app = Flask(__name__)
config = Config('.', os.environ['MOUNT_DIR'], True)

@app.route('/')
def get_index():
    args = dict(zoom=16, lat=37.318373, lon=-122.028352, fields=None)
    args.update(scene_url=url_for('get_scene'))
    return render_template('index.html', **args)

@app.route('/<run_id>/scene.yaml')
@app.route('/scene.yaml')
def get_scene(run_id=None):
    tile_args = dict(zoom=123, col=456, row=789, ext='mvt')
    if run_id:
        tile_args.update(run_id=run_id)
    tile_url = url_for('get_one_tile', **tile_args).replace('123/456/789', '{z}/{x}/{y}')

    return Response(render_template('scene.yaml', tile_url=tile_url),
        headers={'Content-Type': 'application/x-yaml'})

@app.route('/<run_id>/')
def get_run(run_id):
    dirpath = os.path.join(config.dirpath, config.mbtiles_dir)
    url = uritemplate.expand(slippymaps_url_template, dict(run_id=run_id))
    
    try:
        zoom, lat, lon, fields = get_claypigeon_metadata(url, dirpath)
    except TypeError:
        return 'Nope'
    else:
        args = dict(run_id=run_id, zoom=zoom, lat=lat, lon=lon, fields=fields)
        args.update(scene_url=url_for('get_scene', run_id=run_id))
        return render_template('index.html', **args)

@app.route('/<run_id>/<int:zoom>/<int:col>/<int:row>.<ext>')
@app.route('/<run_id>/<int:zoom>/<int:col>/<int:row>')
@app.route('/<int:zoom>/<int:col>/<int:row>.<ext>')
@app.route('/<int:zoom>/<int:col>/<int:row>')
def get_one_tile(zoom, col, row, ext='json', run_id=None):
    if run_id:
        url = uritemplate.expand(slippymaps_url_template, dict(run_id=run_id))
    else:
        # fall back to a recent California dataset.
        url = 'http://s3.amazonaws.com/dotmaps.openaddresses.io/us-ca-monthly/set_141476.mbtiles'
    mime, body = get_url_tile(config, url, row, col, zoom, ext)
    headers = {'Content-Type': mime}
    if ext == 'mvt':
        headers.update({'Content-Encoding': 'gzip'})
    return Response(body, headers=headers)
