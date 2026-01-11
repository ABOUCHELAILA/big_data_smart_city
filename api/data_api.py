from flask import Flask, jsonify, request
from flask_cors import CORS
import requests, json, os

app = Flask(__name__)
CORS(app)

HDFS_NAMENODE = os.getenv('HDFS_NAMENODE', 'http://namenode:9870')
PROCESSED_PATH = '/data/processed/traffic'

def read_hdfs_json(path):
    try:
        list_url = f"{HDFS_NAMENODE}/webhdfs/v1{path}?op=LISTSTATUS"
        res = requests.get(list_url, timeout=5)
        files = res.json().get('FileStatuses', {}).get('FileStatus', [])
        json_files = [f['pathSuffix'] for f in files if f['pathSuffix'].endswith('.json')]
        if not json_files: return []
        read_url = f"{HDFS_NAMENODE}/webhdfs/v1{path}/{json_files[0]}?op=OPEN"
        res = requests.get(read_url, timeout=5)
        return [json.loads(line) for line in res.text.strip().split('\n') if line]
    except: return []

@app.route('/search', methods=['POST'])
def search():
    return jsonify(['zone_metrics', 'congestion', 'road_metrics', 'hourly_patterns'])

@app.route('/query', methods=['POST'])
def query():
    req = request.get_json()
    results = []
    for target in req.get('targets', []):
        t = target.get('target', '')
        if t == 'zone_metrics':
            data = read_hdfs_json(f"{PROCESSED_PATH}/zone_metrics")
            results.append({"columns": [{"text": "Zone"}, {"text": "Trafic"}], "rows": [[d['zone'], d['avg_vehicle_count']] for d in data], "type": "table"})
        elif t == 'road_metrics':
            data = read_hdfs_json(f"{PROCESSED_PATH}/road_metrics")
            # Format spécial pour camembert : une série par type de route
            for d in data:
                results.append({"target": d['road_type'], "datapoints": [[d['avg_speed'], 1]]})
        elif t == 'hourly_patterns':
            data = read_hdfs_json(f"{PROCESSED_PATH}/hourly_patterns")
            results.append({"columns": [{"text": "Heure"}, {"text": "Véhicules"}], "rows": [[f"{d['hour']}h", d['avg_vehicle_count']] for d in data], "type": "table"})
        elif t == 'congestion':
            data = read_hdfs_json(f"{PROCESSED_PATH}/congestion_analysis")
            avg_c = sum(d['congestion_percentage'] for d in data)/len(data) if data else 0
            results.append({"target": "Congestion", "datapoints": [[avg_c, 1]]})
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)