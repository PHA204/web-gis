"""
Script để authenticate Google Earth Engine
"""
import ee

print("=" * 70)
print("     GOOGLE EARTH ENGINE AUTHENTICATION")
print("=" * 70)
print("\n🔐 Bắt đầu quá trình xác thực...")
print("\n📝 Các bước thực hiện:")
print("1. Một cửa sổ trình duyệt sẽ mở ra")
print("2. Đăng nhập bằng Google Account của bạn")
print("3. Cho phép quyền truy cập")
print("4. Copy mã xác thực và paste vào terminal")
print("\n" + "=" * 70)

try:
    # Authenticate
    ee.Authenticate()
    
    print("\n✅ Xác thực thành công!")
    print("\n🔧 Bây giờ hãy thử chạy lại script get_gee_data.py")
    
except Exception as e:
    print(f"\n❌ Lỗi xác thực: {e}")
    print("\n🔧 Hướng dẫn khắc phục:")
    print("1. Kiểm tra kết nối internet")
    print("2. Đảm bảo bạn có Google Account")
    print("3. Thử lại")