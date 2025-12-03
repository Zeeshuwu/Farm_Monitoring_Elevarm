
import ee
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import sqlite3
from dataclasses import dataclass
import logging
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET
import os
import sys
import time
import math


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)


def initialize_earth_engine():
    """Initialize Google Earth Engine with multiple fallback options"""
    try:
        ee.Initialize()
        print("✅ Google Earth Engine initialized successfully")
        return True
    except Exception as e:
        print(f"⚠️ EE initialization failed: {e}")
        print("🧪 Will use MOCK DATA for testing")
        return False


EE_INITIALIZED = False

@dataclass
class ProcessingResult:
    """Data class for processing results"""
    farm_id: str
    date: str
    variable_name: str
    value: float
    cloud_cover: float

class SatelliteIndex(ABC):
    """Abstract base class for satellite indices"""
    
    @abstractmethod
    def calculate(self, image: ee.Image) -> ee.Image:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass

class NDVIIndex(SatelliteIndex):
    def calculate(self, image: ee.Image) -> ee.Image:
        return image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    
    def get_name(self) -> str:
        return 'NDVI'

class EVIIndex(SatelliteIndex):
    def calculate(self, image: ee.Image) -> ee.Image:
        return image.expression(
            '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
            {
                'NIR': image.select('B8'),
                'RED': image.select('B4'),
                'BLUE': image.select('B2')
            }
        ).rename('EVI')
    
    def get_name(self) -> str:
        return 'EVI'

class IndexFactory:
    _indices = {'NDVI': NDVIIndex, 'EVI': EVIIndex}
    
    @classmethod
    def create_index(cls, index_name: str) -> SatelliteIndex:
        if index_name not in cls._indices:
            raise ValueError(f"Unknown index: {index_name}")
        return cls._indices[index_name]()
    
    @classmethod
    def get_available_indices(cls) -> List[str]:
        return list(cls._indices.keys())

def parse_complex_kml_to_geojson(kml_file_path: str) -> Dict:
    """Parse your complex KML file and extract farm boundaries"""
    
    print(f"🔍 Parsing complex KML file: {kml_file_path}")
    
    if not os.path.exists(kml_file_path):
        raise FileNotFoundError(f"KML file not found: {kml_file_path}")
    
    try:
        tree = ET.parse(kml_file_path)
        root = tree.getroot()
        
     
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        print(f"🏷️ Root tag: {root.tag}")
        print(f"📄 Document name: {root.find('.//kml:name', ns).text if root.find('.//kml:name', ns) is not None else 'Unknown'}")
        
        
        placemarks = root.findall('.//kml:Placemark', ns)
        if not placemarks:
            placemarks = root.findall('.//Placemark')
        
        print(f"📍 Found {len(placemarks)} placemarks")
        
       
        farm_polygons = []
        all_coordinates = []
        
        for i, placemark in enumerate(placemarks):
          
            name_elem = placemark.find('.//kml:name', ns) or placemark.find('.//name')
            name = name_elem.text if name_elem is not None else f"Placemark_{i}"
            
            
            polygon = placemark.find('.//kml:Polygon', ns) or placemark.find('.//Polygon')
            if polygon is not None:
                coords_elem = polygon.find('.//kml:coordinates', ns) or polygon.find('.//coordinates')
                if coords_elem is not None and coords_elem.text:
                    coords_text = coords_elem.text.strip()
                    print(f"  🔷 Polygon '{name}': {len(coords_text)} characters")
                    
                  
                    coordinates = []
                    coord_pairs = coords_text.split()
                    
                    for coord_pair in coord_pairs:
                        if coord_pair.strip():
                            try:
                                parts = coord_pair.split(',')
                                if len(parts) >= 2:
                                    lon, lat = float(parts[0]), float(parts[1])
                                    coordinates.append([lon, lat])
                                    all_coordinates.append([lon, lat])
                            except ValueError:
                                continue
                    
                    if len(coordinates) >= 3:
                       
                        if coordinates[0] != coordinates[-1]:
                            coordinates.append(coordinates[0])
                        
                        farm_polygons.append({
                            "name": name,
                            "coordinates": coordinates,
                            "type": "Polygon"
                        })
                        print(f"    ✅ Added polygon with {len(coordinates)} points")
        
        print(f"📊 Found {len(farm_polygons)} valid farm polygons")
        
        if not farm_polygons:
            print("⚠️ No polygons found, looking for points to create bounding area...")
            
          
            points = []
            for placemark in placemarks:
                point = placemark.find('.//kml:Point', ns) or placemark.find('.//Point')
                if point is not None:
                    coords_elem = point.find('.//kml:coordinates', ns) or point.find('.//coordinates')
                    if coords_elem is not None and coords_elem.text:
                        coord_text = coords_elem.text.strip()
                        try:
                            parts = coord_text.split(',')
                            if len(parts) >= 2:
                                lon, lat = float(parts[0]), float(parts[1])
                                points.append([lon, lat])
                        except ValueError:
                            continue
            
            if points:
                print(f"📍 Found {len(points)} points, creating bounding area")
                
                
                lons = [p[0] for p in points]
                lats = [p[1] for p in points]
                
                min_lon, max_lon = min(lons), max(lons)
                min_lat, max_lat = min(lats), max(lats)
                
               
                padding = 0.001
                min_lon -= padding
                max_lon += padding
                min_lat -= padding
                max_lat += padding
                
                bounding_coords = [
                    [min_lon, min_lat],
                    [max_lon, min_lat],
                    [max_lon, max_lat],
                    [min_lon, max_lat],
                    [min_lon, min_lat]  
                ]
                
                return {
                    "type": "Polygon",
                    "coordinates": [bounding_coords],
                    "source": "bounding_area",
                    "point_count": len(points)
                }
        
        
        if len(farm_polygons) == 1:
            coords = farm_polygons[0]["coordinates"]
            return {
                "type": "Polygon",
                "coordinates": [coords],
                "source": "single_polygon",
                "name": farm_polygons[0]["name"]
            }
        
        elif len(farm_polygons) > 1:
           
            largest_polygon = max(farm_polygons, key=lambda p: len(p["coordinates"]))
            print(f" Using largest polygon: '{largest_polygon['name']}' with {len(largest_polygon['coordinates'])} points")
            
            return {
                "type": "Polygon",
                "coordinates": [largest_polygon["coordinates"]],
                "source": "largest_polygon",
                "name": largest_polygon["name"],
                "total_polygons": len(farm_polygons)
            }
        
        else:
       
            print("⚠️ No valid geometry found, using fallback area")
            fallback_coords = [
                [106.9120, -6.7010],
                [106.9150, -6.7010], 
                [106.9150, -6.6980],
                [106.9120, -6.6980],
                [106.9120, -6.7010]
            ]
            
            return {
                "type": "Polygon",
                "coordinates": [fallback_coords],
                "source": "fallback"
            }
        
    except ET.ParseError as e:
        print(f"❌ XML parsing error: {e}")
        raise ValueError(f"Invalid XML in KML file: {e}")
    except Exception as e:
        print(f"❌ Error parsing KML file: {str(e)}")
        raise

def load_megamendung_geometry() -> Dict:
    
    
    print(" Loading Double U Farm Megamendung geometry...")
    print(f" Current working directory: {os.getcwd()}")
    
    # Try to find your KML file
    possible_paths = [
        'data/megamendung.kml',
        'data\\megamendung.kml',
        './data/megamendung.kml',
        os.path.join('data', 'megamendung.kml'),
        os.path.join(project_root, 'data', 'megamendung.kml')
    ]
    
    kml_path = None
    for path in possible_paths:
        if os.path.exists(path):
            kml_path = path
            break
    
    if kml_path is None:
        print("❌ KML file not found!")
        raise FileNotFoundError("Could not find megamendung.kml file")
    
    print(f" Found KML file at: {kml_path}")
    
    try:
        geometry = parse_complex_kml_to_geojson(kml_path)
        print(f" Loaded farm geometry: {geometry.get('source', 'unknown')} source")
        print(f" Geometry: {len(geometry['coordinates'][0])} boundary points")
        
       
        coords = geometry['coordinates'][0]
        if len(coords) > 3:
            lons = [c[0] for c in coords[:-1]]  
            lats = [c[1] for c in coords[:-1]]
            
            lon_range = max(lons) - min(lons)
            lat_range = max(lats) - min(lats)
            
            
            area_deg2 = lon_range * lat_range
            area_m2 = area_deg2 * (111000 ** 2)  
            area_ha = area_m2 / 10000
            
            print(f" Estimated farm area: ~{area_ha:.1f} hectares")
        
        return geometry
        
    except Exception as e:
        print(f" Error loading KML: {e}")
        raise

class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            data_dir = os.path.join(project_root, 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'farm_monitoring.db')
        
        self.db_path = db_path
        print(f"Database path: {self.db_path}")
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS satellite_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    farm_id TEXT NOT NULL,
                    date DATE NOT NULL,
                    variable_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    cloud_cover REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(farm_id, date, variable_name)
                )
            """)
        print(" Database initialized")
    
    def save_results(self, results: List[ProcessingResult]):
        """Save processing results to database"""
        with sqlite3.connect(self.db_path) as conn:
            for result in results:
                conn.execute("""
                    INSERT OR REPLACE INTO satellite_data 
                    (farm_id, date, variable_name, value, cloud_cover)
                    VALUES (?, ?, ?, ?, ?)
                """, (result.farm_id, result.date, result.variable_name, 
                     result.value, result.cloud_cover))
        print(f" Saved {len(results)} results to database")
    
    def get_farm_data(self, farm_id: str, variable: Optional[str] = None) -> Dict:
        """Retrieve farm data from database"""
        with sqlite3.connect(self.db_path) as conn:
            if variable:
                query = """
                    SELECT date, variable_name, value 
                    FROM satellite_data 
                    WHERE farm_id = ? AND variable_name = ?
                    ORDER BY date
                """
                params = (farm_id, variable)
            else:
                query = """
                    SELECT date, variable_name, value 
                    FROM satellite_data 
                    WHERE farm_id = ?
                    ORDER BY date, variable_name
                """
                params = (farm_id,)
            
            df = pd.read_sql_query(query, conn, params=params)
            
            result = {"farm_id": farm_id, "data": {}}
            
            for var_name in df['variable_name'].unique():
                var_data = df[df['variable_name'] == var_name]
                result["data"][var_name] = [
                    {"date": row['date'], "value": row['value']}
                    for _, row in var_data.iterrows()
                ]
            
            return result

class FarmExtractor:
    """Main class for extracting farm satellite data"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        self.logger = self._setup_logging()
        self.ee_available = EE_INITIALIZED
    
    def _setup_logging(self) -> logging.Logger:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def process_farm(self, farm_id: str, geometry: Dict, variables: List[str],
                    start_date: str = "2024-01-01", end_date: str = "2024-12-31") -> Dict:
        """Process farm data using mock data (since EE is not available)"""
        
        self.logger.info(f" Processing farm {farm_id} with MOCK data")
        self.logger.info(f" Geometry source: {geometry.get('source', 'unknown')}")
        self.logger.info(f" Variables: {variables}")
        
        try:
            results = []
            
            # Create sample dates
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Generate data every 16 days (Sentinel-2 revisit)
            current_date = start
            while current_date <= end:
                for var_name in variables:
                    # Generate realistic values based on variable type and season
                    if var_name == "NDVI":
                        base_value = 0.75  # High NDVI for healthy vegetation
                        seasonal_variation = 0.1
                    elif var_name == "EVI":
                        base_value = 0.45  # Corresponding EVI value
                        seasonal_variation = 0.08
                    else:
                        base_value = 0.6
                        seasonal_variation = 0.1
                    
                    # Add seasonal variation (higher in rainy season)
                    days_from_start = (current_date - start).days
                    seasonal_factor = seasonal_variation * np.sin(2 * np.pi * days_from_start / 365)
                    
                    # Add some random variation
                    noise = np.random.normal(0, 0.03)
                    
                    # Simulate weather effects
                    weather_factor = np.random.normal(0, 0.02)
                    
                    value = base_value + seasonal_factor + noise + weather_factor
                    value = max(0.1, min(0.95, value))  # Realistic bounds
                    
                    # Random cloud cover
                    cloud_cover = np.random.uniform(5, 40)
                    
                    results.append(ProcessingResult(
                        farm_id=farm_id,
                        date=current_date.strftime('%Y-%m-%d'),
                        variable_name=var_name,
                        value=float(value),
                        cloud_cover=float(cloud_cover)
                    ))
                
                current_date += timedelta(days=16)  #
            
            
            if results:
                self.db_manager.save_results(results)
                self.logger.info(f" Generated and saved {len(results)} mock data points")
                
                return {
                    "status": "success",
                    "message": f"Generated {len(results)} mock data points for Double U Farm",
                    "results_count": len(results),
                    "note": "This is mock data - Earth Engine not available",
                    "farm_info": {
                        "geometry_source": geometry.get('source'),
                        "boundary_points": len(geometry['coordinates'][0]),
                        "area_estimate": geometry.get('area_ha', 'unknown')
                    }
                }
            else:
                return {
                    "status": "no_data",
                    "message": "No data generated"
                }
                
        except Exception as e:
            self.logger.error(f"Error in processing: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_farm_data(self, farm_id: str, variable: Optional[str] = None) -> Dict:
        """Get processed farm data"""
        return self.db_manager.get_farm_data(farm_id, variable)


if __name__ == "__main__":
    print(" Testing Double U Farm Megamendung Extractor...")
    print("=" * 70)
    
   
    extractor = FarmExtractor()
    
   
    try:
        farm_geometry = load_megamendung_geometry()
        print(f" Successfully loaded farm geometry")
    except Exception as e:
        print(f"❌ Error loading KML: {e}")
        exit(1)
    
    
    print("\nProcessing Double U Farm...")
    result = extractor.process_farm(
        farm_id="double_u_farm_megamendung",
        geometry=farm_geometry,
        variables=["NDVI", "EVI"],
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    
    print("\n Processing result:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    

    if result["status"] == "success":
        print("\n Retrieving processed data...")
        data = extractor.get_farm_data("double_u_farm_megamendung")
        print(f"Farm ID: {data['farm_id']}")
        print("Available variables:", list(data["data"].keys()))
        
        
        for var_name, values in data["data"].items():
            print(f"\n{var_name} ({len(values)} data points):")
            if values:
                print(f"  First: {values[0]['date']} = {values[0]['value']:.3f}")
                print(f"  Last:  {values[-1]['date']} = {values[-1]['value']:.3f}")
                
        
                vals = [v['value'] for v in values]
                print(f"  Mean:  {np.mean(vals):.3f}")
                print(f"  Range: {min(vals):.3f} - {max(vals):.3f}")
    
    print("\n" + "=" * 70)
    print("🎉 Double U Farm Extractor test complete!")
