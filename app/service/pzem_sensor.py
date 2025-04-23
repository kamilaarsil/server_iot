import modbus_tk.modbus_rtu as modbus_rtu
import serial
import time
import struct
from modbus_tk import defines as cst 
import httpx

# Konfigurasi port serial
PORT = "/dev/ttyUSB0"  # Ganti dengan port USB-TTL Anda
api_url = "http://localhost:8000/pzem/create"

async def read_pzem_data():
    try:
        # Membuka koneksi serial
        serial_connection = serial.Serial(
            port=PORT,
            baudrate=9600,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1
        )

        # Membuat master Modbus RTU
        master = modbus_rtu.RtuMaster(serial_connection)
        master.set_timeout(2.0)
        master.set_verbose(True)

        # Membaca register dari PZEM-004T
        slave_id = 0x01  # Default slave ID dari PZEM-004T
        address = 0x0000
        length = 10

        data = master.execute(slave_id, cst.READ_INPUT_REGISTERS, address, length)

        # Parsing data dari register
        voltage = data[0] / 10.0
        current = (data[1] + (data[2] << 16)) / 1000.0
        power = (data[3] + (data[4] << 16)) / 10.0
        energy = data[5] + (data[6] << 16)
        frequency = data[7] / 10.0
        power_factor = data[8] / 100.0

        # Kirim data ke API
        data_to_send = {
            "voltage": voltage,
            "current": current,
            "power": power,
            "energy": energy,
            "frequency": frequency,
            "power_factor": power_factor
        }

        await store_data(data_to_send)

    except httpx.HTTPStatusError as e:
        print(f"Failed to store data: {e}")

async def store_data(data):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://localhost:8000/pzem/create", json=data)
            response.raise_for_status()
            print("PZEM data stored successfully")
        except httpx.HTTPStatusError as e:
            print(f"PZEM failed to store data: {e}")

def calculate_crc(data):
    """Calculate CRC-16 (Modbus standard)"""
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return struct.pack('<H', crc)

def reset_energy_counter():
    try:
        serial_connection = serial.Serial(
            port=PORT,
            baudrate=9600,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1
        )

        slave_id = 0x01
        function_code = 0x42  # Reset function
        reset_command = bytes([slave_id, function_code])  
        reset_command += calculate_crc(reset_command)  # Add CRC

        serial_connection.write(reset_command)
        time.sleep(1)  # Give some time for the reset

        print("Energy reset command sent.")

    except Exception as e:
        print("Error resetting energy:", e)

    finally:
        if 'serial_connection' in locals() and serial_connection.is_open:
            serial_connection.close()