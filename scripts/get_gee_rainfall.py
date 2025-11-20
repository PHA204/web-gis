import ee
import pandas as pd
import psycopg2

# 1. Khởi tạo GEE
ee.Initialize()

# 2. Polygon Quảng Trị
gadm = ee.FeatureCollection("FAO/GAUL/2015/level1")
qt = gadm.filter(ee.Filter.eq('ADM1_NAME', 'Quang Tri')).geometry()

# 3. Lấy dữ liệu CHIRPS 2020
collection = (
    ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
    .filterBounds(qt)
    .filterDate("2020-01-01", "2020-12-31")
)

def extract_rainfall(img):
    date = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd').getInfo()
    mean = img.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=qt,
        scale=5000,
        maxPixels=1e13
    ).get('precipitation').getInfo()
    return {'date': date, 'rainfall_mm': mean}

images = collection.toList(collection.size())
data = [extract_rainfall(images.get(i)) for i in range(collection.size().getInfo())]

df = pd.DataFrame(data)

# 4. Lưu vào PostgreSQL
conn = psycopg2.connect(
    dbname="weather_db",
    user="postgres",
    password="123456",
    host="localhost",
    port=5432
)
cur = conn.cursor()

location_id = 1
source = "CHIRPS"

for _, row in df.iterrows():
    cur.execute("""
        INSERT INTO rainfall_data (location_id, date, rainfall_mm, source)
        VALUES (%s, %s, %s, %s)
    """, (location_id, row['date'], row['rainfall_mm'], source))

conn.commit()
cur.close()
conn.close()
print("Đã lưu dữ liệu vào DB")
