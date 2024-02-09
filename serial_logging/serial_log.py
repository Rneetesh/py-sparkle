import os
import csv
import time
import serial
import datetime
import keyboard
from rich import print
from prettytable import PrettyTable

from lib.usb_selector import list_all_ports

# Get the directory of the Python script
script_directory = os.path.dirname(__file__)
# Set the current working directory to the script's directory
os.chdir(script_directory)
# Get the current working directory
current_directory = os.getcwd()
print("Current Directory:", current_directory)

# Define file path for logging
time_stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
file_path = f"{current_directory}/logs/{time_stamp}.csv"

# Set constants
# Set total number of devices to be used here
# Uncomment or comment lines below based on input type
# total_devices = int(input("Total Number of Devices--"))
total_devices: int = 5

failure_threshold: int = 50
max_tries: int = 3
data_exist: bool = False
device_status: dict = {}
STATUS_ONLINE: str = "ONLINE"
STATUS_OFFLINE: str = "OFFLINE"
STATUS_FAILED: str = "FAILED"

# Define CSV header(colums)
header = ['DATE',
          'TIMESTAMP',
          'DEVICE_ID',
          'TEMP_SETP',
          'OFF_TIME',
          'PWR_LEVEL',
          'CTRL_MODE',
          'IND_FAULT',
          'IND_VOLT',
          'IGBT_CURRENT',
          'IGBT_TEMP',
          'TEMP_POT',
          'TEMP_PROBE'
        ]

# Create a PrettyTable object for displaying device status
table = PrettyTable()

# # Get all connected devices
devices: dict = list_all_ports()
print(devices)
time.sleep(1)


################################################################################################################
def setup_devices():
    # Setup initial status for devices.
    for key, value in devices.items():
        device_status[key] = [value, STATUS_ONLINE, 0, 0]

    if len(device_status) < total_devices:
        for i in range(len(device_status), total_devices):
            device_status[i+1] = ['NC', STATUS_OFFLINE, 0, 0]


################################################################################################################
# Parse data string received from devices.
def parse_ind_data_string(data_raw):
    data_list = []
    data_exist = False

    if "IND-DATA" in data_raw:
        print("[yellow]Found device data!!!")
        data_raw = data_raw.split("{")[1].split("}")[0]
        pairs = data_raw.split(',')
        
        for pair in pairs:
            key, value = pair.split(':')
            if '"' in value:
                value = value.replace('"', '')
            data_list.append(value)

        data_list.pop(0)
        data_exist = True

    return data_exist, data_list


################################################################################################################
# Log data to CSV file.
def log_data_to_csv(device, log_data):
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    current_date = datetime.datetime.now().date()

    log_data.insert(0, device)
    log_data.insert(0, current_time)
    log_data.insert(0, current_date)
    print("Data to be logged-- {}".format(log_data))

    with open(file_path, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=header)
        log_dict = dict(zip(header, log_data))
        
        if not os.path.isfile(file_path):
            writer.writeheader()
        else:
            writer.writerow(log_dict)


################################################################################################################
# Print device status in a pretty table.
def pretty_print():
    os.system('cls' if os.name == 'nt' else 'clear')
    table.clear()
    
    table.field_names = ['DEVICE ID', 'COM PORT', 'STATUS', 'NO RESPONSE', 'RESPONDED']
    for device_id, info in device_status.items():
        table.add_row([device_id] + info)
    
    print(table)
    print("[yellow]HOLD 'SPACE KEY' TO EXIT")
    print("...........................................................")


################################################################################################################
# Update device status based on port changes
def update_devices():
    devices = list_all_ports()
    
    # Create a mapping of COM ports to device IDs in the current 'device_status'
    current_com_to_device = {status[0]: device_id for device_id, status in device_status.items()}

    # Create a mapping of COM ports to device IDs in the updated 'devices'
    updated_com_to_device = {port: device_id for device_id, port in devices.items()}
    
    # print("Updated COM to Device", updated_com_to_device)
    # print("Current COM to Device", current_com_to_device)

    # If a device was disconnected
    for current_port, current_device_id in current_com_to_device.items():
        if current_port not in updated_com_to_device:
            device_status[current_device_id][0] = 'NC'
            device_status[current_device_id][1] = STATUS_OFFLINE

    # Update 'device_status' based on changes in 'devices'
    for port, _ in updated_com_to_device.items():
        # If the COM port is already in 'device_status'
        if port in current_com_to_device:
            current_device_id = current_com_to_device[port]
            device_status[current_device_id][0] = port
            # If it is a reset case set device to online
            if device_status[current_device_id][1] == STATUS_OFFLINE:
                device_status[current_device_id][1] = STATUS_ONLINE
                device_status[current_device_id][2] = 0
                device_status[current_device_id][3] = 0
        
        # If the COM port is not in 'device_status', find a free device ID
        else:
            for current_port, current_device_id in current_com_to_device.items():
                if current_port == 'NC':
                    device_status[current_device_id][0] = port
                    device_status[current_device_id][1] = STATUS_ONLINE
                    device_status[current_device_id][2] = 0
                    device_status[current_device_id][3] = 0


################################################################################################################
################################################# MAIN  ########################################################
################################################################################################################
# Main function to run the logging process
def main():
    print("[yellow]Unplug all other USB devices.")
    print("[green]Setting up the devices...")
    time.sleep(3)

    start_time: float = time.time()
    current_time: float = 0

    setup_devices()
    pretty_print()
    time.sleep(1)

    while True:
        current_time = time.time()

        if keyboard.is_pressed('space'):
            break

        for device, status in (device_status).items():
            update_devices()
            pretty_print()

            # Read only if a device is online
            if status[1] == STATUS_ONLINE:
                try:
                    port_num = status[0]
                    print("[cyan]Reading from DEVICE_{} at {}".format(device, port_num))
                    ser = serial.Serial(port_num, 115200, timeout=2, xonxoff=False, rtscts=False, dsrdtr=False)

                    # Try to read & find log data
                    for _ in range(max_tries):
                        try:
                            ser.flushInput()
                            ser.flushOutput()
                            data_raw = ser.readline()
                            data_raw = data_raw.decode()
                            data_raw = data_raw.strip()
                            # print("[magenta]Raw Data-- {}".format(data_raw))

                            # Get "data_raw" parsed into file logging format
                            data_exist, log_data = parse_ind_data_string(data_raw)
                    
                            # Log into file if particular data was found 
                            if data_exist:
                                device_status[device][3] += 1
                                log_data_to_csv(device, log_data)
                                break

                        except Exception as e:
                            print("[red]Error-- {}".format(e))
                            print("[cyan]Device {} USB disconnected, please reconnect".format(device))
                            device_status[device][1] = STATUS_OFFLINE
                            time.sleep(1)
                            break

                except Exception as e:
                    print("Port Access Error-- {}".format(e))
                
                finally:
                    ser.close()
                
                if not data_exist:
                    device_status[device][2] += 1
                
                if device_status[device][2] > failure_threshold:
                    device_status[device][1] = STATUS_FAILED

                # Reset the failure count after every 30 min. if device is online
                if current_time > start_time + 1800 and device_status[device][1] == STATUS_ONLINE:
                    device_status[device][2] = 0
                    start_time = time.time()

            else:
                print("[red]Device_{} is not connected.".format(device))

            if keyboard.is_pressed('space'):
                break

            time.sleep(1)


################################################################################################################
################################################################################################################
if __name__ == "__main__":
    main()
    print("[yellow]Exiting the logging...")