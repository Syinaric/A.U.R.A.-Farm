"""
Camera test script to verify webcam access on macOS.
Press 'q' to quit.
"""
import cv2

cap = cv2.VideoCapture(0)  # try 1 if black

if not cap.isOpened():
    raise SystemExit("Camera not available. Try index 1 and allow Camera access in macOS settings.")

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    ok, frame = cap.read()
    if not ok:
        break
    # Flip frame horizontally (mirror effect)
    frame = cv2.flip(frame, 1)
    cv2.imshow("Camera Test (q quits)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

