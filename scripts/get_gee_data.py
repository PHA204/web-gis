"""
scripts/get_gee_data.py
Script để lấy dữ liệu lượng mưa và nhiệt độ từ Google Earth Engine
"""

import ee
import pandas as pd
import psycopg2
from datetime import datetime, timedelta

# ================== CẤU HÌNH ==================
# Cấu hình database
DB_CONFIG = {
    'dbname': 'web_gis',
    'user': 'postgres',
    'password': '123456',
    'host': 'localhost',
    'port': 5432
}

# Cấu hình khu vực và thời gian
PROVINCE = "Quang Tri"
LOCATION_ID = 1
START_DATE = "2020-01-01"
END_DATE = "2020-12-31"

# ===============================================
ee.Authenticate()
def initialize_gee():
    """Khởi tạo Google Earth Engine"""
    try:
        # Thử khởi tạo không cần project (cho tài khoản miễn phí)
        try:
            ee.Initialize()
            print("✅ Đã kết nối Google Earth Engine thành công! (No project)")
            return True
        except:
            # Nếu thất bại, thử với project
            ee.Initialize(project='where-earthengine')
            print("✅ Đã kết nối Google Earth Engine thành công! (With project)")
            return True
            
    except Exception as e:
        print(f"❌ Lỗi khi khởi tạo GEE: {e}")
        print("\n🔧 Hướng dẫn khắc phục:")
        print("1. Chạy lệnh: earthengine authenticate")
        print("2. Đăng nhập và cấp quyền")
        print("3. Nếu có nhiều project, set default:")
        print("   earthengine set_project YOUR_PROJECT_ID")
        print("4. Chạy lại script này")
        return False

def get_region_geometry(province_name):
    """Lấy geometry của tỉnh từ GADM"""
    try:
        gadm = ee.FeatureCollection("FAO/GAUL/2015/level1")
        region = gadm.filter(ee.Filter.eq('ADM1_NAME', province_name))
        
        # Kiểm tra xem có tìm thấy không
        count = region.size().getInfo()
        if count == 0:
            print(f"⚠️  Không tìm thấy '{province_name}'. Thử các tên khác:")
            print("   - Quảng Trị")
            print("   - Quang Tri")
            return None
        
        print(f"✅ Đã tìm thấy khu vực: {province_name}")
        return region.geometry()
    except Exception as e:
        print(f"❌ Lỗi khi lấy geometry: {e}")
        return None

def get_rainfall_data(geometry, start_date, end_date, location_id):
    """Lấy dữ liệu lượng mưa từ CHIRPS"""
    print(f"\n🌧️  Đang lấy dữ liệu lượng mưa từ {start_date} đến {end_date}...")
    
    try:
        collection = (
            ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
        )
        
        size = collection.size().getInfo()
        print(f"   Tìm thấy {size} ngày dữ liệu")
        
        if size == 0:
            print("⚠️  Không có dữ liệu trong khoảng thời gian này")
            return pd.DataFrame()
        
        def extract_rainfall(img):
            date = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd').getInfo()
            
            mean_value = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geometry,
                scale=5000,
                maxPixels=1e13
            ).get('precipitation')
            
            rainfall = mean_value.getInfo() if mean_value else 0
            
            return {
                'location_id': location_id,
                'date': date,
                'rainfall_mm': round(rainfall, 2) if rainfall else 0,
                'source': 'CHIRPS'
            }
        
        images = collection.toList(collection.size())
        data = []
        
        for i in range(size):
            try:
                result = extract_rainfall(ee.Image(images.get(i)))
                data.append(result)
                
                if (i + 1) % 30 == 0:
                    print(f"   ⏳ Đã xử lý {i + 1}/{size} ngày ({((i+1)/size*100):.1f}%)")
            except Exception as e:
                print(f"   ⚠️  Lỗi tại ngày {i}: {e}")
        
        print(f"✅ Hoàn thành! Đã lấy {len(data)} bản ghi lượng mưa")
        return pd.DataFrame(data)
        
    except Exception as e:
        print(f"❌ Lỗi khi lấy dữ liệu lượng mưa: {e}")
        return pd.DataFrame()

def get_temperature_data(geometry, start_date, end_date, location_id):
    """Lấy dữ liệu nhiệt độ từ ERA5"""
    print(f"\n🌡️  Đang lấy dữ liệu nhiệt độ từ {start_date} đến {end_date}...")
    
    try:
        collection = (
            ee.ImageCollection("ECMWF/ERA5/DAILY")
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .select(['mean_2m_air_temperature', 'minimum_2m_air_temperature', 
                     'maximum_2m_air_temperature'])
        )
        
        size = collection.size().getInfo()
        print(f"   Tìm thấy {size} ngày dữ liệu")
        
        if size == 0:
            print("⚠️  Không có dữ liệu trong khoảng thời gian này")
            return pd.DataFrame()
        
        def extract_temperature(img):
            date = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd').getInfo()
            
            stats = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geometry,
                scale=25000,
                maxPixels=1e13
            )
            
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
        data = []
        
        for i in range(size):
            try:
                result = extract_temperature(ee.Image(images.get(i)))
                data.append(result)
                
                if (i + 1) % 30 == 0:
                    print(f"   ⏳ Đã xử lý {i + 1}/{size} ngày ({((i+1)/size*100):.1f}%)")
            except Exception as e:
                print(f"   ⚠️  Lỗi tại ngày {i}: {e}")
        
        print(f"✅ Hoàn thành! Đã lấy {len(data)} bản ghi nhiệt độ")
        return pd.DataFrame(data)
        
    except Exception as e:
        print(f"❌ Lỗi khi lấy dữ liệu nhiệt độ: {e}")
        return pd.DataFrame()

def save_to_database(df, table_name):
    """Lưu DataFrame vào PostgreSQL"""
    if df.empty:
        print(f"⚠️  Không có dữ liệu để lưu vào {table_name}")
        return
    
    print(f"\n💾 Đang lưu {len(df)} bản ghi vào bảng {table_name}...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        saved_count = 0
        error_count = 0
        
        for _, row in df.iterrows():
            try:
                if table_name == 'rainfall_data':
                    cur.execute("""
                        INSERT INTO rainfall_data (location_id, date, rainfall_mm, source)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (location_id, date) DO UPDATE 
                        SET rainfall_mm = EXCLUDED.rainfall_mm,
                            source = EXCLUDED.source
                    """, (row['location_id'], row['date'], row['rainfall_mm'], row['source']))
                
                elif table_name == 'temperature_data':
                    cur.execute("""
                        INSERT INTO temperature_data 
                        (location_id, date, temp_min, temp_max, temp_mean, source)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (location_id, date) DO UPDATE 
                        SET temp_min = EXCLUDED.temp_min,
                            temp_max = EXCLUDED.temp_max,
                            temp_mean = EXCLUDED.temp_mean,
                            source = EXCLUDED.source
                    """, (row['location_id'], row['date'], row['temp_min'], 
                          row['temp_max'], row['temp_mean'], row['source']))
                
                saved_count += 1
                
            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    print(f"   ⚠️  Lỗi khi lưu dòng: {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Đã lưu thành công {saved_count}/{len(df)} bản ghi")
        if error_count > 0:
            print(f"⚠️  Có {error_count} lỗi khi lưu")
        
    except Exception as e:
        print(f"❌ Lỗi kết nối database: {e}")
        print("\n🔧 Kiểm tra:")
        print("1. PostgreSQL đã chạy chưa?")
        print("2. Database 'web_gis' đã tạo chưa?")
        print("3. Đã tạo UNIQUE constraints chưa? (chạy add_constraints.py)")

def main():
    """Hàm chính"""
    print("=" * 70)
    print("         🌍 GOOGLE EARTH ENGINE DATA EXTRACTION")
    print("=" * 70)
    
    # Khởi tạo GEE
    if not initialize_gee():
        return
    
    # Lấy geometry
    print(f"\n🗺️  Khu vực: {PROVINCE}")
    geometry = get_region_geometry(PROVINCE)
    
    if geometry is None:
        print("❌ Không thể tiếp tục vì không tìm thấy khu vực")
        return
    
    # Lấy dữ liệu lượng mưa
    print("\n" + "=" * 70)
    print("                    🌧️  DỮ LIỆU LƯỢNG MƯA")
    print("=" * 70)
    rainfall_df = get_rainfall_data(geometry, START_DATE, END_DATE, LOCATION_ID)
    
    if not rainfall_df.empty:
        print(f"\n📊 Preview 5 dòng đầu:")
        print(rainfall_df.head())
        save_to_database(rainfall_df, 'rainfall_data')
    
    # Lấy dữ liệu nhiệt độ
    print("\n" + "=" * 70)
    print("                    🌡️  DỮ LIỆU NHIỆT ĐỘ")
    print("=" * 70)
    temp_df = get_temperature_data(geometry, START_DATE, END_DATE, LOCATION_ID)
    
    if not temp_df.empty:
        print(f"\n📊 Preview 5 dòng đầu:")
        print(temp_df.head())
        save_to_database(temp_df, 'temperature_data')
    
    # Tổng kết
    print("\n" + "=" * 70)
    print("                       ✅ HOÀN THÀNH!")
    print("=" * 70)
    print(f"✓ Lượng mưa: {len(rainfall_df)} bản ghi")
    print(f"✓ Nhiệt độ: {len(temp_df)} bản ghi")
    print("=" * 70)

if __name__ == "__main__":
    main()