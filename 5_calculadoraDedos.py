import cv2
import numpy as np

cap = cv2.VideoCapture(0)

stage = "num1"
num1 = None
num2 = None
operacion = None
resultado = None

def detectar_dedos(frame, x0=50, y0=50, x1=550, y1=550):
    roi = frame[y0:y1, x0:x1]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (35, 35), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    finger_count = 0
    
    if contours:
        cnt = max(contours, key=lambda x: cv2.contourArea(x))
        hull_points = cv2.convexHull(cnt)
        cv2.drawContours(roi, [cnt], -1, (128, 128, 128), 4)
        cv2.drawContours(roi, [hull_points], -1, (128, 128, 128), 4)
        hull = cv2.convexHull(cnt, returnPoints=False)
        defects = cv2.convexityDefects(cnt, hull)
        if defects is not None:
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                start = tuple(cnt[s][0])
                end = tuple(cnt[e][0])
                far = tuple(cnt[f][0])
                a = np.linalg.norm(np.array(end) - np.array(start))
                b = np.linalg.norm(np.array(far) - np.array(start))
                c = np.linalg.norm(np.array(end) - np.array(far))
                angle = np.arccos((b**2 + c**2 - a**2) / (2*b*c))
                if angle <= np.pi/2:
                    finger_count += 1
                    cv2.circle(roi, far, 12, (0,0,0), -1)
    return finger_count, thresh

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    finger_count, thresh = detectar_dedos(frame)
    x0, y0, x1, y1 = 50, 50, 550, 550
    cv2.rectangle(frame, (x0, y0), (x1, y1), (255,255,255), 2)
    overlay = frame.copy()
    if stage == "num1":
        stage_text = "Detecta primer numero (ESPACIO para confirmar)"
    elif stage == "operacion":
        stage_text = "Ingresa operacion (+, -, *, /)"
    elif stage == "num2":
        stage_text = "Detecta segundo numero (ESPACIO para confirmar)"
    elif stage == "resultado":
        stage_text = f"Resultado: {resultado} (ESPACIO para continuar, ENTER para reiniciar)"
    (text_width, text_height), _ = cv2.getTextSize(stage_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
    cv2.rectangle(overlay, (10,10), (10 + text_width + 10, 10 + text_height + 10), (0,0,0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    cv2.putText(frame, stage_text, (15, 10 + text_height), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2, cv2.LINE_AA)
    current_number_text = f"Numero actual: {finger_count+1}"
    (num_width, num_height), _ = cv2.getTextSize(current_number_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
    cv2.rectangle(overlay, (x0, y1 + 10), (x0 + num_width + 10, y1 + 10 + num_height + 5), (0,0,0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    cv2.putText(frame, current_number_text, (x0 + 5, y1 + 10 + num_height), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2, cv2.LINE_AA)
    cv2.imshow("Calculadora con manos", frame)
    cv2.imshow("Threshold", thresh)
    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break
    if key == 32:
        if stage == "num1":
            num1 = finger_count + 1
            stage = "operacion"
        elif stage == "num2":
            num2 = finger_count + 1
            try:
                if operacion == "+":
                    resultado = num1 + num2
                elif operacion == "-":
                    resultado = num1 - num2
                elif operacion == "*":
                    resultado = num1 * num2
                elif operacion == "/":
                    resultado = num1 / num2
                else:
                    resultado = "Operacion invalida"
            except:
                resultado = "Error"
            stage = "resultado"
        elif stage == "resultado":
            num1 = resultado
            stage = "operacion"
    if stage == "operacion":
        if key in [ord('+'), ord('-'), ord('*'), ord('/')]:
            operacion = chr(key)
            stage = "num2"
    if key == 13:
        stage = "num1"
        num1 = num2 = resultado = operacion = None

cap.release()
cv2.destroyAllWindows()