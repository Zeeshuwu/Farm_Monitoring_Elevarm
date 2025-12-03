from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os
import sys
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.farm_extractor import FarmExtractor, load_megamendung_geometry

app = Flask(__name__, 
           template_folder=os.path.join(project_root, 'templates'),
           static_folder=os.path.join(project_root, 'static'))
CORS(app)

extractor = FarmExtractor()

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/api/farm/status')
def farm_status():
    try:
        geometry = load_megamendung_geometry()
        return jsonify({
            "status": "active",
            "farm_name": "Double U Farm Megamendung",
            "location": "Megamendung, West Java, Indonesia",
            "geometry_source": geometry.get('source', 'unknown'),
            "boundary_points": len(geometry['coordinates'][0]),
            "last_updated": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/farm/data')
def get_farm_data():
    variable = request.args.get('variable')
    try:
        data = extractor.get_farm_data("double_u_farm_megamendung", variable)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/farm/process', methods=['POST'])
def process_farm():
    try:
        data = request.get_json() or {}
        variables = data.get('variables', ['NDVI', 'EVI'])
        start_date = data.get('start_date', '2024-01-01')
        end_date = data.get('end_date', '2024-12-31')
        
        geometry = load_megamendung_geometry()
        result = extractor.process_farm(
            farm_id="double_u_farm_megamendung",
            geometry=geometry,
            variables=variables,
            start_date=start_date,
            end_date=end_date
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/farm/latest')
def get_latest_data():
    try:
        data = extractor.get_farm_data("double_u_farm_megamendung")
        latest_data = {}
        for variable, values in data["data"].items():
            if values:
                latest_data[variable] = values[-1]
        
        return jsonify({
            "farm_id": data["farm_id"],
            "latest_readings": latest_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/farm/summary')
def get_farm_summary():
    try:
        data = extractor.get_farm_data("double_u_farm_megamendung")
        summary = {
            "farm_id": data["farm_id"],
            "variables": {},
            "total_readings": 0
        }
        
        for variable, values in data["data"].items():
            if values:
                vals = [v['value'] for v in values]
                summary["variables"][variable] = {
                    "count": len(values),
                    "latest": values[-1],
                    "mean": sum(vals) / len(vals),
                    "min": min(vals),
                    "max": max(vals),
                    "trend": "stable"
                }
                summary["total_readings"] += len(values)
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
