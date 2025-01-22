import time
from lewansoul_servo_bus import ServoBus

# Inicializa a comunicação
servo_bus = ServoBus('COM3')  # mudar no ubuntu


# MOTOR 1: limitar a 90 graus
# MOTOR 2: limitar a 15 graus
# IDs
PAN_SERVO_ID = 1
TILT_SERVO_ID = 2

# default angles
PAN_STANDBY_ANGLE = 140
TILT_STANDBY_ANGLE = 150

# faixa de valores aceitavel
PAN_VALUES = 90
TIL_VALUES = 15

# Limites para os ângulos de pan e tilt
PAN_MIN_ANGLE = PAN_STANDBY_ANGLE - PAN_VALUES
PAN_MAX_ANGLE = PAN_STANDBY_ANGLE + PAN_VALUES
TILT_MIN_ANGLE = TILT_STANDBY_ANGLE - TIL_VALUES
TILT_MAX_ANGLE = TILT_STANDBY_ANGLE + TIL_VALUES

PAN_PIXELS = 1280   # Largura da imagem em pixels
TILT_PIXELS = 720  # Altura da imagem em pixels
PAN_FOV = 120       # Campo de visão horizontal em graus
TILT_FOV = 60       # Campo de visão vertical em graus


def pixels_to_angle(pixels, max_pixels, fov, min_angle, max_angle):
    """Converte um número de pixels em ângulos respeitando os limites."""
    angle = (pixels / max_pixels) * fov
    return max(min_angle, min(max_angle, angle))


def set_servo_angle(servo_id, angle, duration):
    """Define o ângulo do servo especificado com um tempo de movimento."""
    if 0 <= angle <= 240:  # Limite de angulo permitido pela biblioteca
        servo_bus.move_time_write(servo_id, angle, duration)
    else:
        print(f"Erro: Ângulo {angle} fora do limite permitido (0-240 graus).")


def main():
    # Colocar os servos em posição de standby
    set_servo_angle(PAN_SERVO_ID, PAN_STANDBY_ANGLE, 5)
    set_servo_angle(TILT_SERVO_ID, TILT_STANDBY_ANGLE, 5)
    print("Controle de Pan e Tilt iniciado. Pressione Ctrl+C para sair.")
    try:
        while True:
            # Obtenha os ângulos de entrada externa
            try:
                pan_angle = float(input("angulo de PAN (0-240): "))
                tilt_angle = float(input("angulo de TILT (0-240): "))
                duration = int(input("tempo (s): "))
            except ValueError:
                print("Por favor, insira valores válidos para os ângulos e o tempo.")
                continue

            # Ajusta os motores para os ângulos recebidos
            # Garantir que os ângulos estejam dentro dos limites definidos
            pan_angle = max(PAN_MIN_ANGLE, min(PAN_MAX_ANGLE, pan_angle))
            tilt_angle = max(TILT_MIN_ANGLE, min(TILT_MAX_ANGLE, tilt_angle))

            set_servo_angle(PAN_SERVO_ID, pan_angle, duration)
            set_servo_angle(TILT_SERVO_ID, tilt_angle, duration)

            # Aguardar um curto período antes de receber novos comandos
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nEncerrando o controle de Pan e Tilt.")


if __name__ == "__main__":
    main()
