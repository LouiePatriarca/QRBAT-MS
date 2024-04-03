import serial
import time

# Configure the serial port
ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)

def send_sms(number, message):
    # AT command to set SIM800L to text mode
    ser.write(b'AT+CMGF=1\r\n')
    time.sleep(1)

    # AT command to set the phone number
    ser.write(b'AT+CMGS="' + number.encode() + b'"\r\n')
    time.sleep(1)

    # Sending the message
    ser.write(message.encode() + b"\r\n")
    time.sleep(1)

    # End the message with CTRL+Z
    ser.write(bytes([26]))
    time.sleep(1)

    # Read the response
    response = ser.readlines()
    print(response)

# Example usage
send_sms("+639564925360", "Hello from your Python app!")

# Close the serial port
ser.close()