import json
import time
import cv2
import numpy as np
import paho.mqtt.client as mqtt

from lewansoul_servo_bus import ServoBus

# -------------------------------------------------------------
# Configurações do MQTT
BROKER_ADDRESS = "broker.emqx.io"  # ou "localhost", etc.
BROKER_PORT = 1883
TOPIC_POS = "camera/pos"          # Tópico para receber bounding boxes
TOPIC_ESCOLHA = "camera/escolha"  # Tópico para publicar a escolha
TOPIC_ESCOLHA_RES = "camera/escolhaRes"  # Tópico que retorna deltaX/deltaY
TOPIC_IMAGEM = "camera/imagem"    # Tópico com a imagem (se necessário)

# -------------------------------------------------------------
# Inicializa comunicação com os servos (ajustar se necessário)
servo_bus = ServoBus('COM3')  # ou a porta correspondente no seu sistema

PAN_SERVO_ID = 1
TILT_SERVO_ID = 2

# Ângulos iniciais "standby"
PAN_STANDBY_ANGLE = servo_bus.pos_read(PAN_SERVO_ID)
TILT_STANDBY_ANGLE = servo_bus.pos_read(TILT_SERVO_ID)

# Limites
PAN_VALUES = 15
TIL_VALUES = 90
PAN_MIN_ANGLE = PAN_STANDBY_ANGLE - PAN_VALUES
PAN_MAX_ANGLE = PAN_STANDBY_ANGLE + PAN_VALUES
TILT_MIN_ANGLE = TILT_STANDBY_ANGLE - TIL_VALUES
TILT_MAX_ANGLE = TILT_STANDBY_ANGLE + TIL_VALUES

PAN_PIXELS = 1280  # Largura da imagem
TILT_PIXELS = 720  # Altura da imagem
PAN_FOV = 120
TILT_FOV = 60


def pixels_to_angle(pixels, max_pixels, fov):
    """Converte um número de pixels em ângulos respeitando os limites."""
    angle = (pixels / max_pixels) * fov
    return -angle


def set_servo_angle(servo_id, angle, duration=2):
    """Define o ângulo do servo especificado com um tempo de movimento."""
    if 0 <= angle <= 240:  # Limite de angulo permitido pela lib
        servo_bus.move_time_write(servo_id, angle, duration)
    else:
        print(f"Erro: Ângulo {angle} fora do limite permitido (0-240 graus).")

# -------------------------------------------------------------
# Variáveis globais (para simplificar) em que armazenaremos dados
bboxes_global = []  # para armazenar bounding boxes recebidos
ultima_imagem = None

# -------------------------------------------------------------
# Callbacks MQTT


def on_connect(client, userdata, flags, rc):
    """Callback de conexão ao broker."""
    if rc == 0:
        print("Conectado ao broker MQTT!")
        # Inscrever-se nos tópicos relevantes
        client.subscribe(TOPIC_POS)
        client.subscribe(TOPIC_ESCOLHA_RES)
        client.subscribe(TOPIC_IMAGEM)
    else:
        print(f"Falha na conexão. Código de retorno = {rc}")


def on_message(client, userdata, msg):
    """Callback chamado quando chega mensagem em algum tópico inscrito."""
    global bboxes_global, ultima_imagem

    if msg.topic == TOPIC_POS:
        # Recebemos a lista de bounding boxes
        try:
            bboxes = json.loads(msg.payload.decode("utf-8"))
            bboxes_global = bboxes  # Armazena para uso posterior
            print("Bounding boxes recebidas:")
            if not bboxes:
                print("Nenhum objeto detectado no momento.")
                return
            for i, obj in enumerate(bboxes):
                tag = obj.get('tag', 'obj')
                conf = obj.get('box', [0, 0, 0, 0, 0])[-1]
                print(f"[{i}] -> {tag} ({conf*100:.0f}%)")

            # Pergunta ao usuário qual índice deseja (opcional)
            choice_str = input("Digite o índice do objeto desejado: ")
            try:
                choice_idx = int(choice_str)
            except ValueError:
                print("Entrada inválida (não é número). Retornando.")
                return

            # Publicar escolha no tópico TOPIC_ESCOLHA
            escolha_msg = {"index": choice_idx}
            print(f"Publicando escolha = {escolha_msg} no tópico {TOPIC_ESCOLHA}...")
            client.publish(TOPIC_ESCOLHA, json.dumps(escolha_msg))

        except Exception as e:
            print("Falha ao processar bounding boxes:", e)

    elif msg.topic == TOPIC_ESCOLHA_RES:
        # Recebemos a resposta com deltaX, deltaY
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            deltaX = data.get("deltaX", 0)
            deltaY = data.get("deltaY", 0)
            objTag = data.get("objTag", "desconhecido")
            print(f"Resposta à escolha recebida:")
            print(f"  Objeto: {objTag}")
            print(f"  deltaX: {deltaX}")
            print(f"  deltaY: {deltaY}")

            # Movimenta servos conforme deltaX, deltaY
            # Coloca primeiro o servo em standby
            set_servo_angle(PAN_SERVO_ID, PAN_STANDBY_ANGLE, 2)
            time.sleep(2)
            set_servo_angle(TILT_SERVO_ID, TILT_STANDBY_ANGLE, 2)
            time.sleep(2)

            pan_angle = pixels_to_angle(deltaX, PAN_PIXELS, PAN_FOV)
            tilt_angle = pixels_to_angle(deltaY, TILT_PIXELS, TILT_FOV)

            # Ajusta com base no ângulo "standby"
            pan_angle = -pan_angle + PAN_STANDBY_ANGLE
            tilt_angle = tilt_angle + TILT_STANDBY_ANGLE

            # Respeita limites
            pan_angle = max(PAN_MIN_ANGLE, min(PAN_MAX_ANGLE, pan_angle))
            tilt_angle = max(TILT_MIN_ANGLE, min(TILT_MAX_ANGLE, tilt_angle))

            print(f"Movendo servo pan para {pan_angle} e tilt para {tilt_angle}")
            set_servo_angle(PAN_SERVO_ID, pan_angle, 2)
            time.sleep(2)
            set_servo_angle(TILT_SERVO_ID, tilt_angle, 2)
            time.sleep(2)

        except Exception as e:
            print("Falha ao processar resposta de escolha:", e)

    elif msg.topic == TOPIC_IMAGEM:
        # Recebemos a imagem bruta (bytes) pelo tópico MQTT
        try:
            np_image = np.frombuffer(msg.payload, dtype=np.uint8)
            image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
            if image is None:
                print("Falha ao decodificar a imagem recebida via MQTT.")
                return
            ultima_imagem = image  # Armazena se quiser usar mais tarde

            # Desenhar bounding boxes (se já as tivermos em bboxes_global)
            for result in bboxes_global:
                box = result.get("box", [])
                tag = result.get("tag", "obj")
                if len(box) < 5:
                    continue

                left, top, right, bottom, confidence = box
                left, top, right, bottom = map(int, [left, top, right, bottom])

                cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
                label = f"{tag} {int(confidence*100)}%"
                cv2.putText(
                    image,
                    label,
                    (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA
                )

            # Exibe a imagem
            cv2.imshow("Resultado MQTT", image)
            cv2.waitKey(1)  # se usar 0, ele congela o loop

        except Exception as e:
            print("Erro ao processar imagem MQTT:", e)

# -------------------------------------------------------------
# Função principal


def main():
    # Ajusta servos em standby no início
    set_servo_angle(PAN_SERVO_ID, PAN_STANDBY_ANGLE, 2)
    time.sleep(2)
    set_servo_angle(TILT_SERVO_ID, TILT_STANDBY_ANGLE, 2)
    time.sleep(2)

    # Cria cliente MQTT
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Conecta-se ao broker
    print(f"Conectando ao broker {BROKER_ADDRESS}:{BROKER_PORT}...")
    client.connect(BROKER_ADDRESS, BROKER_PORT, keepalive=60)

    try:
        # Loop infinito para ouvir mensagens
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nEncerrando...")
    finally:
        # Coloca servos em standby ao encerrar
        set_servo_angle(PAN_SERVO_ID, PAN_STANDBY_ANGLE, 2)
        set_servo_angle(TILT_SERVO_ID, TILT_STANDBY_ANGLE, 2)
        cv2.destroyAllWindows()

# -------------------------------------------------------------


if __name__ == "__main__":
    main()
