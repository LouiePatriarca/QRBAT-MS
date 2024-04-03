import serial
import time

# Configure the serial port
ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)

def send_command(command):
    ser.write(command.encode() + b'\r\n')
    time.sleep(0.1)
    return ser.readlines()

def read_sms(index):
    response = send_command('AT+CMGF=1')  # Set SMS mode to text
    response = send_command('AT+CMGR=' + str(index))  # Read SMS at index
    return response

# Example usage
sms_index = 1  # Index of the SMS you want to read
response = read_sms(sms_index)
for line in response:
    print(line.strip().decode())

# Close the serial port
ser.close()