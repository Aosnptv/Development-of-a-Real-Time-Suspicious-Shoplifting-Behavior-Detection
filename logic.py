import math

class SuspiciousTracker:
    def __init__(self):
        self.score = 0
        self.threshold = 5

    def calculate_distance(self, box1, box2):
        # คำนวณจุดกึ่งกลางของกล่องวัตถุ
        x1, y1 = (box1[0] + box1[2])/2, (box1[1] + box1[3])/2
        x2, y2 = (box2[0] + box2[2])/2, (box2[1] + box2[3])/2
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    def update_score(self, hand_box, item_box):
        if hand_box and item_box:
            dist = self.calculate_distance(hand_box, item_box)
            # ถ้าระยะห่างน้อยกว่า 100 pixel (สมมติว่าคือการหยิบ/สัมผัส)
            if dist < 100:
                self.score += 1
                print(f"พฤติกรรมเสี่ยง! คะแนนปัจจุบัน: {self.score}")
                
        if self.score >= self.threshold:
            return True # เกินกำหนด แจ้งเตือน!
        return False