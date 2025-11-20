"""
scripts/get_gee_data.py
Script để lấy dữ liệu lượng mưa và nhiệt độ từ Google Earth Engine
"""

import ee
import pandas as pd
import psycopg2
from datetime import datetime, timedelta

# Khởi tạo GEE (cần authenticate trước: earthengine authenticate)
ee.Initialize()

# Cấu hình database
DB_CONFIG = {
    'dbname': 'web_gis',
    'user': 'postgres',
    'password': '123456',
    'host': 'localhost',
    'port': 5432
}

def get_region_geometry(province_name):
    """Lấy geometry của tỉnh từ GADM"""
    gadm = ee.FeatureCollection("FAO/GAUL/2015/level1")
    region = gadm.filter(ee.Filter.eq('ADM1_NAME', province_name))
    return region.geometry()

def get_rainfall_data(geometry, start_date, end_date, location_id):
    """Lấy dữ liệu lượng mưa từ CHIRPS"""
    print(f"Đang lấy dữ liệu lượng mưa từ {start_date} đến {end_date}...")
    
    collection = (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
    )
    
    def extract_rainfall(img):
        date = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd').getInfo()
        
        # Tính trung bình cho khu vực
        mean_value = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=5000,
            maxPixels=1e13
        ).get('precipitation')
        
        # Xử lý trường hợp None
        rainfall = mean_value.getInfo() if mean_value else 0
        
        return {
            'location_id': location_id,
            'date': date,
            'rainfall_mm': round(rainfall, 2) if rainfall else 0,
            'source': 'CHIRPS'
        }
    
    # Lấy danh sách các image
    images = collection.toList(collection.size())
    size = collection.size().getInfo()
    
    data = []
    for i in range(size):
        try:
            result = extract_rainfall(images.get(i))
            data.append(result)
            if (i + 1) % 30 == 0:
                print(f"  Đã xử lý {i + 1}/{size} ngày")
        except Exception as e:
            print(f"  Lỗi tại index {i}: {e}")
    
    return pd.DataFrame(data)

def get_temperature_data(geometry, start_date, end_date, location_id):
    """Lấy dữ liệu nhiệt độ từ ERA5"""
    print(f"Đang lấy dữ liệu nhiệt độ từ {start_date} đến {end_date}...")
    
    collection = (
        ee.ImageCollection("ECMWF/ERA5/DAILY")
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .select(['mean_2m_air_temperature', 'minimum_2m_air_temperature', 
                 'maximum_2m_air_temperature'])
    )
    
    def extract_temperature(img):
        date = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd').getInfo()
        
        stats = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=25000,
            maxPixels=1e13
        )
        
        # Chuyển từ Kelvin sang Celsius
        temp_mean = stats.get('mean_2m_air_temperature')
        temp_min = stats.get('minimum_2m_air_temperature')
        temp_max = stats.get('maximum_2m_air_temperature')
        
        return {
            'location_id': location_id,
            'date': date,
            'temp_mean': round(temp_mean.getInfo() - 273.15, 2) if temp_mean else None,
            'temp_min': round(temp_min.getInfo() - 273.15, 2) if temp_min else None,
            'temp_max': round(temp_max.getInfo() - 273.15, 2) if temp_max else None,
            'source': 'ERA5'
        }
    
    images = collection.toList(collection.size())
    size = collection.size().getInfo()
    
    data = []
    for i in range(size):
        try:
            result = extract_temperature(images.get(i))
            data.append(result)
            if (i + 1) % 30 == 0:
                print(f"  Đã xử lý {i + 1}/{size} ngày")
        except Exception as e:
            print(f"  Lỗi tại index {i}: {e}")
    
    return pd.DataFrame(data)

def save_to_database(df, table_name):
    """Lưu DataFrame vào PostgreSQL"""
    print(f"Đang lưu {len(df)} bản ghi vào bảng {table_name}...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    saved_count = 0
    for _, row in df.iterrows():
        try:
            if table_name == 'rainfall_data':
                cur.execute("""
                    INSERT INTO rainfall_data (location_id, date, rainfall_mm, source)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (row['location_id'], row['date'], row['rainfall_mm'], row['source']))
            
            elif table_name == 'temperature_data':
                cur.execute("""
                    INSERT INTO temperature_data 
                    (location_id, date, temp_min, temp_max, temp_mean, source)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (row['location_id'], row['date'], row['temp_min'], 
                      row['temp_max'], row['temp_mean'], row['source']))
            
            saved_count += 1
        except Exception as e:
            print(f"Lỗi khi lưu dòng: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Đã lưu thành công {saved_count} bản ghi")

def main():
    """Hàm chính"""
    print("=" * 60)
    print("SCRIPT LẤY DỮ LIỆU TỪ GOOGLE EARTH ENGINE")
    print("=" * 60)
    
    # Cấu hình
    PROVINCE = "Quang Tri"
    LOCATION_ID = 1
    START_DATE = "2020-01-01"
    END_DATE = "2023-12-31"
    
    # Lấy geometry
    print(f"\n📍 Khu vực: {PROVINCE}")
    geometry = get_region_geometry(PROVINCE)
    
    # Lấy dữ liệu lượng mưa
    print("\n🌧️  DỮ LIỆU LƯỢNG MƯA")
    print("-" * 60)
    rainfall_df = get_rainfall_data(geometry, START_DATE, END_DATE, LOCATION_ID)
    print(f"Đã lấy được {len(rainfall_df)} bản ghi")
    save_to_database(rainfall_df, 'rainfall_data')
    
    # Lấy dữ liệu nhiệt độ
    print("\n🌡️  DỮ LIỆU NHIỆT ĐỘ")
    print("-" * 60)
    temp_df = get_temperature_data(geometry, START_DATE, END_DATE, LOCATION_ID)
    print(f"Đã lấy được {len(temp_df)} bản ghi")
    save_to_database(temp_df, 'temperature_data')
    
    print("\n" + "=" * 60)
    print("✅ HOÀN THÀNH!")
    print("=" * 60)

if __name__ == "__main__":
    main()