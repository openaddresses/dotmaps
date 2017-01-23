import TileStache, ModestMaps
import sqlite3, subprocess, re, os.path, base64, json

WARNING_PAT_TPL = r'^\S+: Warning: using tile \d+/\d+/\d+ instead of {0}/{1}/{2}\n'

class MissingTile (Exception):
    pass

class Config:
    ''' Implements minimal configuration object for TileStache.
    
        See http://tilestache.org/doc/#custom-configuration
        
        mbtiles_dir: directory where MBTiles files are located.
        is_claypigeon: boolean flag for Claypigeon filesystem.
    '''
    def __init__(self, dirpath, mbtiles_dir, is_claypigeon):
        self.cache = TileStache.Caches.Test() # Disk('cache')
        self.layers = Layers(self)
        self.dirpath = dirpath

        self.mbtiles_dir = mbtiles_dir
        self.is_claypigeon = is_claypigeon

class Layers:
    ''' Implements minimal layers stub for TileStache Configuration.
    
        See http://tilestache.org/doc/#custom-configuration
    '''
    def __init__(self, config):
        self.config = config
        self._dict = dict()
    
    def keys(self):
        raise NotImplementedError() # return self._dict.keys()

    def items(self):
        return self._dict.items()

    def __contains__(self, key):
        raise NotImplementedError() # return key in self._dict

    def __getitem__(self, key):
        if key not in self._dict:
            if self.config.is_claypigeon:
                name = base64.b64encode(key.encode('utf8')).decode('ascii')
            else:
                name = key
            path = os.path.join(self.config.dirpath, self.config.mbtiles_dir, name)
            proj = TileStache.Geography.SphericalMercator()
            meta = TileStache.Core.Metatile()
            layer = TileStache.Core.Layer(self.config, proj, meta)
            layer.provider = TippecanoeProvider(layer, path)
            self._dict[key] = layer
        return self._dict[key]

class TippecanoeProvider:
    ''' Accepts requests for tiles from a Tippecanoe MBTiles file.
    '''
    def __init__(self, layer, path):
        self.path = os.path.join(layer.config.dirpath, path)
    
    def renderTile(self, width, height, srs, coord):
        ''' Return a TileWriter instance for a single tile.
        '''
        if coord.zoom <= 14:
            return TileWriter(self.path, coord)
        else:
            raise ValueError('Out of range TippecanoeProvider zoom {}'.format(coord.zoom))
    
    def getTypeByExtension(self, extension):
        if extension.lower() == 'mvt':
            return ('application/x-protobuf', 'MapboxVectorTile')
        elif extension.lower() in ('geojson', 'json'):
            return ('application/json', 'GeoJSON')
        else:
            raise ValueError('Unknown TippecanoeProvider extension {}'.format(extension))

class TileWriter:
    ''' Requests and serializes a single tile from a Tippecanoe MBTiles file.
    '''
    def __init__(self, path, coord):
        self.path = path
        self.coord = coord
        self.zxy = self.coord.zoom, self.coord.column, self.coord.row
    
    def save(self, output, format):
        try:
            if format == 'MapboxVectorTile':
                return self.save_MapboxVectorTile(output)
            elif format == 'GeoJSON':
                return self.save_GeoJSON(output)
            else:
                raise ValueError('Unknown TileWriter format {}'.format(format))
        except MissingTile:
            output.write(b'I am not a tile')
    
    def save_MapboxVectorTile(self, output):
        ''' Write raw MVT bytes from MBTiles row to output.
        '''
        with sqlite3.connect('file:{}?immutable=1'.format(self.path), uri=True) as db:
            tile_row = (2**self.coord.zoom - 1) - self.coord.row
            res = db.execute('''
                SELECT tile_data FROM tiles
                WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?
                ''', (self.coord.zoom, self.coord.column, tile_row))
            try:
                (content, ) = res.fetchone()
            except TypeError:
                raise MissingTile('Missing TileWriter tile {}/{}/{}'.format(*self.zxy))
        output.write(content)
    
    def save_GeoJSON(self, output):
        ''' Write GeoJSON bytes from tippecanoe-decode to output.
        '''
        z, x, y = self.zxy
        command = 'tippecanoe-decode', self.path, str(z), str(x), str(y)
        content = subprocess.check_output(command, stderr=subprocess.STDOUT)
        heading = content[:256].decode('utf8', 'ignore') # should be on line 1
        if 'Warning' in heading:
            warning_pattern = re.compile(WARNING_PAT_TPL.format(*self.zxy))
            if warning_pattern.match(heading):
                raise MissingTile('Missing TileWriter tile {}/{}/{}'.format(*self.zxy))
        output.write(content)

def get_claypigeon_connection(url, dirpath):
    '''
    '''
    name = base64.b64encode(url.encode('utf8')).decode('ascii')
    path = os.path.join(dirpath, name)
    
    return sqlite3.connect('file:{}?immutable=1'.format(path), uri=True)

def get_claypigeon_metadata(url, dirpath):
    '''
    '''
    try:
        connection = get_claypigeon_connection(url, dirpath)
    except sqlite3.OperationalError as e:
        return None
    else:
        with connection as db:
            res = db.execute('''SELECT name, value FROM metadata
                                WHERE name IN ('center', 'json')''')
            
            data = dict(res.fetchall())
            lon, lat, zoom = map(float, data.get('center', '0,0,0').split(','))
            
            print('woo:', json.loads(data.get('json', '{}')))
            
            more = json.loads(data.get('json', '{}'))
            fields = more.get('vector_layers', [])[0].get('fields', {}).keys()

    return zoom, lat, lon, fields

def get_url_tile(config, url, row, col, zoom, ext):
    '''
    '''
    layer = config.layers[url]
    coord = ModestMaps.Core.Coordinate(row, col, zoom) # (1582, 656, 12)
    mime, body = TileStache.getTile(layer, coord, ext)
    return (mime, body)
