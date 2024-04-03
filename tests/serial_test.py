import serial
import time

# Define the serial port and baud rate
ser = serial.Serial('/dev/serial0', 9600)  # Use the correct serial port and baud rate

# Initialize the SIM800L module
ser.write(b'AT\r\n')
time.sleep(1)

ser.write(b'AT+CTPIN?\r\n')
time.sleep(1)

# # Set the SMS mode to text mode
# ser.write(b'AT+CMGF=1\r\n')
# time.sleep(1)


# # Set the recipient's phone number
# ser.write(b'AT+CMGS="+639564925360"\r\n')
# time.sleep(1)


# # Send the SMS message
# message = "Hello, this is a test message from Python!"
# ser.write(message.encode() + b'\x1A\r\n')
# time.sleep(1)


try:
    while True:
        # Read a line of data from the serial port
        data = ser.readline().decode().strip()
        print(data)  # Print the data to the console

except KeyboardInterrupt:
    print("Serial monitoring stopped.")

finally:
    ser.close()  # Close the serial port when done
