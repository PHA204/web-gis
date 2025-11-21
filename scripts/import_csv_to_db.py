"""
Script import dữ liệu từ CSV (export từ GEE) vào PostgreSQL
"""
import pandas as pd
import psycopg2
from pathlib import Path
import sys

# Cấu hình
DB_CONFIG = {
    'dbname': 'web_gis',
    'user': 'postgres',
    'password': '123456',
    'host': 'localhost',
    'port': 5432
}

LOCATION_ID = 1  # ID của Quảng Trị trong bảng locations

def test_connection():
    """Kiểm tra kết nối database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"✅ Kết nối database thành công!")
        print(f"   PostgreSQL version: {version[0][:50]}...")
        
        # Kiểm tra bảng
        cur.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('rainfall_data', 'temperature_data', 'locations')
        """)
        tables = [row[0] for row in cur.fetchall()]
        print(f"   Bảng có sẵn: {', '.join(tables)}")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Lỗi kết nối database: {e}")
        print("\n🔧 Kiểm tra:")
        print("1. PostgreSQL đã chạy chưa?")
        print("2. Database 'web_gis' đã tạo chưa?")
        print("3. Thông tin trong DB_CONFIG có đúng không?")
        return False

def import_rainfall_csv(csv_path):
    """Import dữ liệu lượng mưa từ CSV"""
    print(f"\n🌧️  Đang import dữ liệu lượng mưa từ: {csv_path}")
    
    try:
        # Đọc CSV với encoding phù hợp
        print("   Đọc file CSV...")
        df = pd.read_csv(csv_path, encoding='utf-8')
        print(f"   ✓ Đã đọc {len(df)} dòng từ CSV")
        
        # Hiển thị các cột có trong CSV
        print(f"   Các cột trong CSV: {', '.join(df.columns.tolist())}")
        
        # Kiểm tra các cột cần thiết
        required_cols = ['date', 'rainfall_mm']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"   ❌ Thiếu các cột: {', '.join(missing_cols)}")
            print(f"   📋 Cột có sẵn: {', '.join(df.columns.tolist())}")
            return 0
        
        # Preview dữ liệu
        print(f"\n   📊 Preview 3 dòng đầu:")
        print(df[['date', 'rainfall_mm']].head(3).to_string(index=False))
        
        # Kết nối database
        print("\n   Kết nối database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Đếm số dòng hiện có
        cur.execute("""
            SELECT COUNT(*) FROM rainfall_data 
            WHERE location_id = %s
        """, (LOCATION_ID,))
        existing_count = cur.fetchone()[0]
        print(f"   ℹ️  Số bản ghi hiện có: {existing_count}")
        
        saved_count = 0
        error_count = 0
        
        print(f"\n   💾 Đang lưu dữ liệu...")
        for idx, row in df.iterrows():
            try:
                # Làm sạch dữ liệu
                rainfall = float(row['rainfall_mm']) if pd.notna(row['rainfall_mm']) else 0
                date_str = str(row['date'])
                
                cur.execute("""
                    INSERT INTO rainfall_data (location_id, date, rainfall_mm, source)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (location_id, date) DO UPDATE 
                    SET rainfall_mm = EXCLUDED.rainfall_mm,
                        source = EXCLUDED.source
                """, (LOCATION_ID, date_str, rainfall, 'CHIRPS'))
                
                saved_count += 1
                
                # Hiển thị tiến trình
                if (idx + 1) % 50 == 0:
                    print(f"      ⏳ Đã xử lý {idx + 1}/{len(df)} dòng ({((idx+1)/len(df)*100):.1f}%)")
                    
            except Exception as e:
                error_count += 1
                if error_count <= 5:  # Chỉ hiển thị 5 lỗi đầu
                    print(f"      ⚠️  Lỗi dòng {idx + 1}: {e}")
        
        conn.commit()
        
        # Kiểm tra số lượng sau khi insert
        cur.execute("""
            SELECT COUNT(*) FROM rainfall_data 
            WHERE location_id = %s
        """, (LOCATION_ID,))
        new_count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        print(f"\n   ✅ Hoàn thành!")
        print(f"      • Đã xử lý: {saved_count}/{len(df)} bản ghi")
        print(f"      • Lỗi: {error_count} bản ghi")
        print(f"      • Tổng trong DB: {new_count} bản ghi")
        
        return saved_count
        
    except FileNotFoundError:
        print(f"   ❌ Không tìm thấy file: {csv_path}")
        return 0
    except pd.errors.EmptyDataError:
        print(f"   ❌ File CSV rỗng!")
        return 0
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        return 0

def import_temperature_csv(csv_path):
    """Import dữ liệu nhiệt độ từ CSV"""
    print(f"\n🌡️  Đang import dữ liệu nhiệt độ từ: {csv_path}")
    
    try:
        # Đọc CSV
        print("   Đọc file CSV...")
        df = pd.read_csv(csv_path, encoding='utf-8')
        print(f"   ✓ Đã đọc {len(df)} dòng từ CSV")
        
        # Hiển thị các cột
        print(f"   Các cột trong CSV: {', '.join(df.columns.tolist())}")
        
        # Kiểm tra các cột cần thiết
        required_cols = ['date', 'temp_min', 'temp_max', 'temp_mean']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"   ❌ Thiếu các cột: {', '.join(missing_cols)}")
            print(f"   📋 Cột có sẵn: {', '.join(df.columns.tolist())}")
            return 0
        
        # Preview dữ liệu
        print(f"\n   📊 Preview 3 dòng đầu:")
        print(df[['date', 'temp_min', 'temp_max', 'temp_mean']].head(3).to_string(index=False))
        
        # Kết nối database
        print("\n   Kết nối database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Đếm số dòng hiện có
        cur.execute("""
            SELECT COUNT(*) FROM temperature_data 
            WHERE location_id = %s
        """, (LOCATION_ID,))
        existing_count = cur.fetchone()[0]
        print(f"   ℹ️  Số bản ghi hiện có: {existing_count}")
        
        saved_count = 0
        error_count = 0
        
        print(f"\n   💾 Đang lưu dữ liệu...")
        for idx, row in df.iterrows():
            try:
                # Làm sạch dữ liệu
                temp_min = float(row['temp_min']) if pd.notna(row['temp_min']) else None
                temp_max = float(row['temp_max']) if pd.notna(row['temp_max']) else None
                temp_mean = float(row['temp_mean']) if pd.notna(row['temp_mean']) else None
                date_str = str(row['date'])
                
                cur.execute("""
                    INSERT INTO temperature_data 
                    (location_id, date, temp_min, temp_max, temp_mean, source)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (location_id, date) DO UPDATE 
                    SET temp_min = EXCLUDED.temp_min,
                        temp_max = EXCLUDED.temp_max,
                        temp_mean = EXCLUDED.temp_mean,
                        source = EXCLUDED.source
                """, (LOCATION_ID, date_str, temp_min, temp_max, temp_mean, 'ERA5'))
                
                saved_count += 1
                
                # Hiển thị tiến trình
                if (idx + 1) % 50 == 0:
                    print(f"      ⏳ Đã xử lý {idx + 1}/{len(df)} dòng ({((idx+1)/len(df)*100):.1f}%)")
                    
            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    print(f"      ⚠️  Lỗi dòng {idx + 1}: {e}")
        
        conn.commit()
        
        # Kiểm tra số lượng sau khi insert
        cur.execute("""
            SELECT COUNT(*) FROM temperature_data 
            WHERE location_id = %s
        """, (LOCATION_ID,))
        new_count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        print(f"\n   ✅ Hoàn thành!")
        print(f"      • Đã xử lý: {saved_count}/{len(df)} bản ghi")
        print(f"      • Lỗi: {error_count} bản ghi")
        print(f"      • Tổng trong DB: {new_count} bản ghi")
        
        return saved_count
        
    except FileNotFoundError:
        print(f"   ❌ Không tìm thấy file: {csv_path}")
        return 0
    except pd.errors.EmptyDataError:
        print(f"   ❌ File CSV rỗng!")
        return 0
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    """Hàm chính"""
    print("=" * 70)
    print("        📥 IMPORT DỮ LIỆU TỪ CSV VÀO POSTGRESQL")
    print("=" * 70)
    
    # Test kết nối trước
    print("\n🔌 Kiểm tra kết nối database...")
    if not test_connection():
        print("\n❌ Không thể kết nối database. Dừng chương trình.")
        sys.exit(1)
    
    # Đường dẫn đến file CSV
    rainfall_csv = "QuangTri_Rainfall_2020.csv"
    temperature_csv = "QuangTri_Temperature_2020.csv"
    
    total_rainfall = 0
    total_temp = 0
    
    # Import lượng mưa
    if Path(rainfall_csv).exists():
        total_rainfall = import_rainfall_csv(rainfall_csv)
    else:
        print(f"\n⚠️  Không tìm thấy file: {rainfall_csv}")
        print(f"   Vị trí hiện tại: {Path.cwd()}")
        print(f"   Các file CSV trong thư mục scripts:")
        scripts_dir = Path("scripts")
        if scripts_dir.exists():
            for f in scripts_dir.glob("*.csv"):
                print(f"      • {f.name}")
    
    # Import nhiệt độ
    if Path(temperature_csv).exists():
        total_temp = import_temperature_csv(temperature_csv)
    else:
        print(f"\n⚠️  Không tìm thấy file: {temperature_csv}")
    
    # Tổng kết
    print("\n" + "=" * 70)
    print("                    ✅ HOÀN THÀNH!")
    print("=" * 70)
    print(f"✓ Lượng mưa: {total_rainfall} bản ghi")
    print(f"✓ Nhiệt độ: {total_temp} bản ghi")
    print("=" * 70)

if __name__ == "__main__":
    main()