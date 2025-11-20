import ee

# Authenticate (mở trình duyệt login)
ee.Authenticate()

# Khởi tạo
# Initialize với project default
ee.Initialize(project='projects/earthengine-legacy')

print("GEE đã sẵn sàng")
