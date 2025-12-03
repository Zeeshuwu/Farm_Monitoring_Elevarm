# 🌾 ELEVARM - Satellite Farm Monitoring System
**Advanced GIS Software Engineering Solution**

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Flask](https://img.shields.io/badge/Flask-2.3.3-red) ![Google Earth Engine](https://img.shields.io/badge/Google%20Earth%20Engine-API-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Table of Contents
- [Overview](#-overview)
- [Technical Challenge](#-technical-challenge)
- [System Architecture](#-system-architecture)
- [Vegetation Indices Explained](#-vegetation-indices-explained)
- [Installation & Setup](#-installation--setup)
- [API Documentation](#-api-documentation)
- [Cloud Masking Strategy](#-cloud-masking-strategy)
- [Project Structure](#-project-structure)
- [Usage Examples](#-usage-examples)

---

## 🎯 Overview

This project addresses PT. Elevasi Agri Indonesia's core engineering challenge:

> **"Can we build a scalable engine that automatically translates messy satellite data into clean, actionable insights for thousands of farms instantly?"**

Farm Monitoring Project is a comprehensive GIS software engineering solution that transforms raw Sentinel-2 satellite imagery into structured, actionable agricultural insights through automated processing pipelines.

### 🏆 Key Achievements
- ✅ **Modular Architecture**: Easily extensible for new vegetation indices
- ✅ **Robust Cloud Masking**: <30% cloud cover threshold with pixel-level masking
- ✅ **RESTful API**: Production-ready endpoints for farm processing and data retrieval
- ✅ **Scalable Design**: Architecture ready for 5,000+ farms
- ✅ **Real-time Dashboard**: Interactive visualization for agronomy teams

---

## 🚀 Technical Challenge

### The Problem
Indonesia's horticulture sector relies heavily on manual inspections and intuition for critical farming decisions. With thousands of farms to manage, manual data collection becomes impossible, necessitating satellite-based monitoring solutions.

### The Solution
A **scalable satellite data processing engine** that:
1. **Ingests** farm geometries and processing parameters.
2. **Processes** Sentinel-2 imagery through Google Earth Engine.
3. **Calculates** multiple vegetation indices (NDVI, EVI, SAVI, NDMI).
4. **Stores** results in structured database format.
5. **Serves** data through high-performance REST API.

---

## 🏗️ System Architecture

### Part A: The Flexible Extractor (Python Worker)
Located in `src/farm_extractor.py`:
```python
class FarmExtractor:
    def process_farm(self, farm_id, geometry, variables, date_range):
        """
        Modular satellite data processing engine
        - Connects to Google Earth Engine
        - Applies cloud masking (<30% threshold)
        - Calculates requested vegetation indices
        - Stores results in SQL database
        """
```

### Part B: The Data API (Flask REST Service)
Located in `src/api.py`:
```python
@app.route('/process-farm', methods=['POST'])
def process_farm():
    """Triggers satellite data processing for specified farm"""

@app.route('/farms/<farm_id>/data', methods=['GET'])
def get_farm_data(farm_id):
    """Returns time-series data optimized for visualization"""
```

### Part C: Scaling Architecture

**🔄 Job Queue System for 5,000+ Farms**
```text
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   API Gateway   │───▶│  Redis Queue │───▶│  Worker Nodes   │
│                 │    │              │    │                 │
│ • Rate Limiting │    │ • Job Queue  │    │ • GEE Processing│
│ • Load Balancer │    │ • Priority   │    │ • DB Storage    │
│ • Request Val.  │    │ • Retry Logic│    │ • Error Handling│
└─────────────────┘    └──────────────┘    └─────────────────┘
```

---

## 🌱 Vegetation Indices Explained
*Why These Indices Matter for Indonesian Agriculture*

### 🟢 NDVI (Normalized Difference Vegetation Index)
`NDVI = (NIR - RED) / (NIR + RED)`
* **Purpose:** Primary vegetation health indicator.
* **Range:** -1 to +1 (higher = healthier vegetation).
* **Indonesian Context:** Critical for rice paddies and palm oil plantations.

### 🌿 EVI (Enhanced Vegetation Index)
`EVI = 2.5 * ((NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1))`
* **Purpose:** Improved sensitivity in high biomass areas.
* **Indonesian Context:** Ideal for tropical forests and dense plantation crops.

### 🏜️ SAVI (Soil Adjusted Vegetation Index)
`SAVI = ((NIR - RED) / (NIR + RED + L)) * (1 + L)`
* **Purpose:** Minimizes soil brightness influence.
* **Indonesian Context:** Perfect for newly planted areas and crop establishment phases.

### 💧 NDMI (Normalized Difference Moisture Index)
`NDMI = (NIR - SWIR1) / (NIR + SWIR1)`
* **Purpose:** Vegetation water content assessment.
* **Indonesian Context:** Critical during dry season monitoring.

---

## 🛠️ Installation & Setup

### Prerequisites
* Python 3.8+
* Google Earth Engine account
* Redis (for queue management)

### 1. Clone Repository
```bash
git clone [https://github.com/your-username/elevarm.git](https://github.com/your-username/elevarm.git)
cd ELEVARM
```

### 2. Environment Setup
```bash
# Activate virtual environment (Windows)
elevarm_env\Scripts\activate

# OR Activate virtual environment (Linux/Mac)
source elevarm_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Google Earth Engine Authentication
```bash
# Authenticate with Google Earth Engine
earthengine authenticate

# Initialize in Python
python -c "import ee; ee.Initialize()"
```

### 4. Configuration
Create a `.env` file in the root directory:
```bash
cp .env.example .env
# Configure DATABASE_URL, GEE_KEY, and REDIS_URL inside .env
```

---

## 📡 API Documentation

### Core Endpoints

#### 1. Process Farm Data
**POST** `/api/v1/process-farm`

**Request:**
```json
{
  "farm_id": "FARM_001",
  "geometry": { "type": "Polygon", "coordinates": [...] },
  "variables": ["NDVI", "EVI"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

#### 2. Get Farm Data
**GET** `/api/v1/farms/FARM_001/data?start_date=2024-01-01&end_date=2024-12-31`

---

## ☁️ Cloud Masking Strategy

**The Challenge:** Indonesian tropical climate presents high cloud frequency (60-80% of images).

**Our Solution: Multi-Layer Cloud Detection**
1.  **Sentinel-2 SCL:** Uses built-in cloud probability > 65%.
2.  **Probability Threshold:** Aggressive 30% threshold filtering.
3.  **Temporal Compositing:** Monthly median composites to fill gaps.

---

## 📁 Project Structure

```text
ELEVARM/
├── .vscode/
│   ├── launch.json
│   └── settings.json
├── data/                         # Local data storage
├── docs/                         # Documentation files
├── elevarm_env/                  # Virtual environment
├── scripts/                      # Utility scripts
├── src/                          # Source code
│   ├── __pycache__/
│   ├── templates/
│   │   └── dashboard.html        # Web interface template
│   ├── api.py                    # Main Flask entry point
│   ├── config.py                 # Configuration loader
│   ├── farm_extractor.py         # GEE processing logic
│   └── init.py                   # Package initialization
├── tests/                        # Unit and integration tests
├── .env                          # Environment variables
├── requirements.txt              # Dependency list
└── test_redis.py                 # Redis connection test
```

---

## 💡 Usage Examples

### 1. Start the API Server
```bash
# Make sure you are in the ELEVARM root directory
python src/api.py
```

### 2. Run Redis Tests
To ensure your job queue connection is working:
```bash
python test_redis.py
```

### 3. Example: Process Single Farm (Python)
```python
import requests

response = requests.post('http://localhost:5000/process-farm', json={
    "farm_id": "RICE_FIELD_001",
    "geometry": { ... },
    "variables": ["NDVI", "EVI"]
})
print(response.json())
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
