from lewansoul_servo_bus import ServoBus
import time

servo_bus = ServoBus('COM3')

# servo_bus.id_write(1, 2)

# Move servo with ID 1 to 90 degrees in 1.0 seconds
servo_bus.move_time_write(1, 145, 1.0)
time.sleep(2)
servo_bus.move_time_write(2, 160, 1.0)
# time.sleep(2)
# servo_bus.move_time_write(2, 95, 1.0)
# time.sleep(2)
# servo_bus.move_time_write(1, 155, 1.0)
# time.sleep(2)
# servo_bus.move_time_write(2, 65, 1.0)
# time.sleep(2)
# servo_bus.move_time_write(1, 140, 1.0)
# time.sleep(2)
# servo_bus.move_time_write(2, 80, 1.0)

# Move servo with ID 2 to 180 degrees in 2.0 seconds
#servo_2 = servo_bus.get_servo(2)
#servo_2.move_time_write(0, 2.0)
