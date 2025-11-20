"""
Script import dữ liệu từ CSV (export từ GEE) vào PostgreSQL
"""
import pandas as pd
import psycopg2
from pathlib import Path

# Cấu hình
DB_CONFIG = {
    'dbname': 'web_gis',
    'user': 'postgres',
    'password': '123456',
    'host': 'localhost',
    'port': 5432
}

LOCATION_ID = 1  # ID của Quảng Trị trong bảng locations

def import_rainfall_csv(csv_path):
    """Import dữ liệu lượng mưa từ CSV"""
    print(f"\n🌧️  Đang import dữ liệu lượng mưa từ: {csv_path}")
    
    try:
        # Đọc CSV
        df = pd.read_csv(csv_path)
        print(f"   Đã đọc {len(df)} dòng từ CSV")
        
        # Kết nối database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        saved_count = 0
        for _, row in df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO rainfall_data (location_id, date, rainfall_mm, source)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (location_id, date) DO UPDATE 
                    SET rainfall_mm = EXCLUDED.rainfall_mm
                """, (LOCATION_ID, row['date'], row['rainfall_mm'], 'CHIRPS'))
                saved_count += 1
            except Exception as e:
                print(f"   ⚠️  Lỗi dòng {_}: {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Đã import thành công {saved_count}/{len(df)} bản ghi lượng mưa")
        return saved_count
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return 0

def import_temperature_csv(csv_path):
    """Import dữ liệu nhiệt độ từ CSV"""
    print(f"\n🌡️  Đang import dữ liệu nhiệt độ từ: {csv_path}")
    
    try:
        # Đọc CSV
        df = pd.read_csv(csv_path)
        print(f"   Đã đọc {len(df)} dòng từ CSV")
        
        # Kết nối database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        saved_count = 0
        for _, row in df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO temperature_data 
                    (location_id, date, temp_min, temp_max, temp_mean, source)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (location_id, date) DO UPDATE 
                    SET temp_min = EXCLUDED.temp_min,
                        temp_max = EXCLUDED.temp_max,
                        temp_mean = EXCLUDED.temp_mean
                """, (LOCATION_ID, row['date'], 
                      row['temp_min'], row['temp_max'], row['temp_mean'], 'ERA5'))
                saved_count += 1
            except Exception as e:
                print(f"   ⚠️  Lỗi dòng {_}: {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Đã import thành công {saved_count}/{len(df)} bản ghi nhiệt độ")
        return saved_count
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return 0

def main():
    """Hàm chính"""
    print("=" * 70)
    print("        📥 IMPORT DỮ LIỆU TỪ CSV VÀO POSTGRESQL")
    print("=" * 70)
    
    # Đường dẫn đến file CSV
    # Thay đổi đường dẫn này theo file của bạn
    rainfall_csv = "QuangTri_Rainfall_2020.csv"
    temperature_csv = "QuangTri_Temperature_2020.csv"
    
    total_rainfall = 0
    total_temp = 0
    
    # Import lượng mưa
    if Path(rainfall_csv).exists():
        total_rainfall = import_rainfall_csv(rainfall_csv)
    else:
        print(f"⚠️  Không tìm thấy file: {rainfall_csv}")
    
    # Import nhiệt độ
    if Path(temperature_csv).exists():
        total_temp = import_temperature_csv(temperature_csv)
    else:
        print(f"⚠️  Không tìm thấy file: {temperature_csv}")
    
    # Tổng kết
    print("\n" + "=" * 70)
    print("                    ✅ HOÀN THÀNH!")
    print("=" * 70)
    print(f"✓ Lượng mưa: {total_rainfall} bản ghi")
    print(f"✓ Nhiệt độ: {total_temp} bản ghi")
    print("=" * 70)

if __name__ == "__main__":
    main()