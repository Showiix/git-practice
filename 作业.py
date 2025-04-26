import abc
import numpy
from datetime import datetime
from collections import defaultdict

# Base Device Class
class Device(abc.ABC):
    def __init__(self, device_id, name, energy_usage=0):
        self.__device_id = device_id
        self.__name = name
        self.__status = 'off'
        self.__energy_usage = energy_usage

    # Getter methods
    def get_id(self):
        return self.__device_id

    def get_name(self):
        return self.__name

    def get_status(self):
        return self.__status

    def get_energy_usage(self):
        return self.__energy_usage

    # Control methods
    def turn_on(self):
        if self.__status != 'on':
            self.__status = 'on'
            self.__energy_usage += 0.1

    def turn_off(self):
        if self.__status != 'off':
            self.__status = 'off'
            self.__energy_usage += 0.02

    def __str__(self):
        return (
            f"Device: {self.get_name()}, ID: {self.get_id()}, "
            f"Status: {self.get_status().upper()}, "
            f"Energy Usage: {self.get_energy_usage():.2f}kWh"
        )

# Subclasses
class Light(Device):
    def __init__(self, device_id, name, brightness=100):
        super().__init__(device_id, name)
        self.__brightness = max(0, min(100, brightness))

class Thermostat(Device):
    def __init__(self, device_id, name, temperature=22):
        super().__init__(device_id, name)
        self.__temperature = max(10, min(30, temperature))

class Camera(Device):
    def __init__(self, device_id, name, resolution='1080p'):
        super().__init__(device_id, name)
        self.__resolution = resolution

# Device Controller
class DeviceController:
    def __init__(self):
        self.devices = {}

    def add_device(self, device):
        device_id = device.get_id()
        if device_id not in self.devices:
            self.devices[device_id] = device
        else:
            print(f"Device {device_id} already exists")

    def remove_device(self, device_id):
        if device_id in self.devices:
            del self.devices[device_id]
            return True
        return False

    def list_devices(self):
        for device in self.devices.values():
            print(device)

    def execute_command(self, device_id, command):
        device = self.devices.get(device_id)
        if device:
            if command == 'on':
                device.turn_on()
                print(f"Executed {command} on {device.get_name()}")
            elif command == 'off':
                device.turn_off()
                print(f"Executed {command} on {device.get_name()}")
            else:
                print(f"Invalid command: {command}")
        else:
            print(f"Device {device_id} not found")

# Smart Home Hub (Singleton)
class SmartHomeHub:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SmartHomeHub, cls).__new__(cls)
            cls._instance.controller = DeviceController()
        return cls._instance

    def schedule_task(self, device_id, command, time):
        print(f"Task scheduled: {command} {device_id} at {time}")

    def display_status(self):
        print("Current Device Status:")
        self.controller.list_devices()

    def total_energy_usage(self):
        devices = list(self.controller.devices.values())
        return self._recursive_sum(devices)

    def _recursive_sum(self, devices):
        if not devices:
            return 0.0
        return devices[0].get_energy_usage() + self._recursive_sum(devices[1:])

# Main Execution
if __name__ == "__main__":
    hub = SmartHomeHub()

    # Create devices
    light = Light("L1", "Living Room Light")
    thermostat = Thermostat("T1", "Home Thermostat")
    camera = Camera("C1", "Front Door Camera")

    # Add devices
    hub.controller.add_device(light)
    hub.controller.add_device(thermostat)
    hub.controller.add_device(camera)

    # Display initial status
    hub.display_status()

    # Execute commands
    hub.controller.execute_command("L1", "on")
    hub.controller.execute_command("T1", "off")

    # Schedule task
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hub.schedule_task("C1", "on", current_time)

    # Display updated status
    print("\nUpdated Status:")
    hub.display_status()

    # Calculate total energy usage
    total_energy = hub.total_energy_usage()
    print(f"\nTotal Energy Usage: {total_energy:.2f} kWh")