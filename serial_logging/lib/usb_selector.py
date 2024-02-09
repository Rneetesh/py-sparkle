import serial.tools.list_ports
from os.path import exists
from rich import print


################################################################ LIST_ALL_PORTS ################################################################
def list_all_ports():
    # Check if the system is Linux-based (such as Raspberry Pi or CM4)
    if exists('/dev/serial0'):
        # Return the predefined CM4 port if it exists
        return ['/dev/serial0']
    
    # Get a list of all available ports
    live_ports = serial.tools.list_ports.comports()
    
    enumerated_ports = list(enumerate(sorted(live_ports)))
    devices: dict = {}

    # Check if any ports are available
    if not enumerated_ports:
        print("[red]No COM ports found, please reconnect and try again...")
    else:
        print("[yellow]Devices Found...")
        # Print information about each port and store it in the 'devices' dictionary
        for n, (port, desc, hwid) in enumerated_ports:
            devices[n+1] = port
    
    return devices


################################################################ GET_SERIAL_DEVICE ################################################################
def get_serial_device(usr=0):
    # Get a list of all available ports
    ports = serial.tools.list_ports.comports()
    
    enumerated_ports = list(enumerate(sorted(ports)))

    # Ensure that the user input is within range
    if usr >= len(enumerated_ports):
        usr = 0

    # Check if any ports are available
    if enumerated_ports:
        try:
            # Get the selected port based on user input
            selected_comm = enumerated_ports[usr][1][0]
            print(f"[cyan]Connecting to {selected_comm}...")
            return selected_comm
            
        except Exception as e:
            print("[red]Error:", e)
            print("[red]Select a valid serial port!!!")
    else:
        print("[red]No COM ports found, please reconnect and try again...")


################################################################################################################################
if __name__ == "__main__":
    list_all_ports()