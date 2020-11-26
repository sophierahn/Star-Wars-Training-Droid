import time
import board
import busio
import adafruit_lidarlite
from multiprocessing import Pipe


# Create library object using our Bus I2C port
i2c = busio.I2C(board.SCL, board.SDA)

# Default configuration, with only i2c wires
sensor = adafruit_lidarlite.LIDARLite(i2c)


def LidarMain(lidar_conn):

    # Create library object using our Bus I2C port
    i2c = busio.I2C(board.SCL, board.SDA)

    # Default configuration, with only i2c wires
    sensor = adafruit_lidarlite.LIDARLite(i2c)

    shutdown = False

    while not shutdown:

        if lidar_conn.poll():
            shutdown = lidar_conn.recv()

        try:
            height = sensor.distance

            lidar_conn.send(height)

        except RuntimeError as e:
            # If we get a reading error, just print it and keep truckin'
            print(e)
        #time.sleep(0.02)  # you can remove this for ultra-fast measurements!
