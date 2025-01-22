import requests
import cv2
import numpy as np
import time
from lewansoul_servo_bus import ServoBus

# Initialize communication
servo_bus = ServoBus('COM3')  # change on ubuntu (Raspberry PI)

# Motors IDs
PAN_SERVO_ID = 1
TILT_SERVO_ID = 2
PAN_STANDBY_ANGLE = 145
TILT_STANDBY_ANGLE = 150
PAN_VALUES = 90
TIL_VALUES = 15
PAN_MIN_ANGLE = PAN_STANDBY_ANGLE - PAN_VALUES
PAN_MAX_ANGLE = PAN_STANDBY_ANGLE + PAN_VALUES
TILT_MIN_ANGLE = TILT_STANDBY_ANGLE - TIL_VALUES
TILT_MAX_ANGLE = TILT_STANDBY_ANGLE + TIL_VALUES

# FOV and resolution of the camera
PAN_PIXELS = 1280
TILT_PIXELS = 720
PAN_FOV = 120
TILT_FOV = 60


def pixels_to_angle(pixels, max_pixels, fov, min_angle, max_angle):
    """Converte pixels em ângulos respeitando os limites."""
    angle = (pixels / max_pixels) * fov
    return -angle


def set_servo_angle(servo_id, angle, duration):
    """Define o ângulo do servo especificado."""
    if 0 <= angle <= 240:
        servo_bus.move_time_write(servo_id, angle, duration)
    else:
        print(f"Erro: Ângulo {angle} fora do limite permitido (0-240 graus).")


def obter_bounding_boxes(base_url):
    try:
        response = requests.get(f"{base_url}/pos", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao obter /pos: {e}")
        return []


def escolher_objeto(base_url, choice_idx):
    try:
        response = requests.get(f"{base_url}/escolha", params={"index": str(choice_idx)}, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao obter /escolha: {e}")
        return {}


def main():
    set_servo_angle(PAN_SERVO_ID, PAN_STANDBY_ANGLE, 5)
    set_servo_angle(TILT_SERVO_ID, TILT_STANDBY_ANGLE, 5)
    time.sleep(6)
    base_url = "http://192.168.0.101:8080"

    bboxes = obter_bounding_boxes(base_url)
    if not bboxes:
        print("Nenhum objeto detectado.")
        return

    for i, obj in enumerate(bboxes):
        tag = obj.get('tag', 'obj')
        conf = obj.get('box', [0,0,0,0,0])[-1]
        print(f"[{i}] -> {tag} ({conf*100:.0f}%)")

    try:
        choice_idx = int(input("Digite o índice do objeto desejado: "))
    except ValueError:
        print("Entrada inválida.")
        return

    resposta = escolher_objeto(base_url, choice_idx)
    deltaX, deltaY = resposta.get("deltaX", 0), resposta.get("deltaY", 0)
    objTag = resposta.get("objTag", "obj?")
    print(f"Objeto: {objTag}, deltaX: {deltaX}, deltaY: {deltaY}")

    pan_angle = pixels_to_angle(deltaX, PAN_PIXELS, PAN_FOV, PAN_MIN_ANGLE, PAN_MAX_ANGLE) + PAN_STANDBY_ANGLE
    tilt_angle = pixels_to_angle(deltaY, TILT_PIXELS, TILT_FOV, TILT_MIN_ANGLE, TILT_MAX_ANGLE) + TILT_STANDBY_ANGLE
    pan_angle = max(PAN_MIN_ANGLE, min(PAN_MAX_ANGLE, pan_angle))
    tilt_angle = max(TILT_MIN_ANGLE, min(TILT_MAX_ANGLE, tilt_angle))

    set_servo_angle(PAN_SERVO_ID, pan_angle, 2)
    set_servo_angle(TILT_SERVO_ID, tilt_angle, 2)
    time.sleep(0.1)


if __name__ == "__main__":
    main()
