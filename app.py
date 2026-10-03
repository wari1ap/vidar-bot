import cv2
import requests
import numpy as np
import time

# ==========================================
# 1. ตั้งค่าการเชื่อมต่อและข้อมูลของคุณ
# ==========================================
RTSP_URL = "http://192.168.1.51:4747/วิดิโอ"
LINE_ACCESS_TOKEN = "jnlApIVgKhlzKwr+VrcJ5qTrb7z3pS0PuGFoHAj9Is3J++VGcUCQBiDK+qctLF+wSAmeQQ+gxwOpSNhCFSctSYf0lQX0HwMLxYfCWY7lvAvled5mxpKu56vdhTrLc+jwQ85FoEPWsgZCHFALoeWwYwdB04t89/1O/w1cDnyilFU="

# URL หรือ IP ของบอร์ด ESP สำหรับสั่งการขับเคลื่อน
ESP_CONTROL_URL = "http://192.168.1.100/control"

# ==========================================
# 2. ฟังก์ชันระบบเสริมและการรายงานสถานะ
# ==========================================
def send_line_message(message, image=None):
    """ส่งข้อความแจ้งเตือนพร้อมรูปภาพ (ถ้ามี) เข้า LINE"""
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    # โครงสร้างสำหรับการส่งการแจ้งเตือน
    print(f"กำลังส่งแจ้งเตือน: {message}")

def get_battery_status():
    """จำลองการดึงสถานะแบตเตอรี่จากระบบฮาร์ดแวร์"""
    # ในอนาคตสามารถเชื่อมต่อผ่าน API ของบอร์ด ESP เพื่อรับค่าจริงได้
    battery_level = 85  # สมมติค่าระดับแบตเตอรี่
    return f"ระดับแบตเตอรี่: {battery_level}%"

def update_module_status(status_text):
    """อัปเดตสถานะของโมดูลใน UI"""
    print(f"[Module Status]: {status_text}")

def control_robot_motors(command):
    """ส่งคำสั่งควบคุมระบบขับเคลื่อนไปยังบอร์ด ESP"""
    try:
        # response = requests.post(ESP_CONTROL_URL, json={"command": command})
        print(f"ส่งคำสั่งควบคุม: {command} ไปยังระบบขับเคลื่อน")
    except Exception as e:
        print(f"ไม่สามารถส่งคำสั่งได้: {e}")

# ==========================================
# 3. เริ่มต้นระบบตรวจจับคน (HOG People Detector)
# ==========================================
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

cap = cv2.VideoCapture(RTSP_URL)
last_send_time = 0
status_update_timer = 0

print("เริ่มการทำงานระบบตรวจจับและรายงานสถานะ...")
update_module_status("ระบบพร้อมทำงาน (Ready)")

while True:
    ret, frame = cap.read()
    if not ret:
        update_module_status("สูญเสียการเชื่อมต่อกับกล้อง")
        print("ไม่สามารถรับสัญญาณภาพจากกล้องได้")
        break

    frame_resized = cv2.resize(frame, (640, 480))
    boxes, _ = hog.detectMultiScale(frame_resized, winStride=(8, 8))

    # ตรวจสอบและแสดงสถานะแบตเตอรี่ทุก ๆ 60 วินาทีใน Logs
    if time.time() - status_update_timer > 60:
        battery_info = get_battery_status()
        print(battery_info)
        status_update_timer = time.time()

    if len(boxes) > 0:
        for (x, y, w, h) in boxes:
            cv2.rectangle(frame_resized, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame_resized, "Person", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # หน่วงเวลาแจ้งเตือนทุก 10 วินาที
        if time.time() - last_send_time > 10:
            update_module_status("ตรวจพบผู้บุกรุก! กำลังแจ้งเตือน")
            battery_info = get_battery_status()
            message = f"ตรวจพบคน! {battery_info}"
            
            # เปิดใช้งานฟังก์ชันสำรองสำหรับระบบขับเคลื่อนเมื่อพบคน
            control_robot_motors("STOP_AND_ALERT")
            
            send_line_message(message)
            last_send_time = time.time()

    cv2.imshow("Sentry Robot - Monitor", frame_resized)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        update_module_status("ระบบปิดการทำงาน")
        break

cap.release()
cv2.destroyAllWindows()
