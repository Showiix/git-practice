import abc
from datetime import datetime
from collections import defaultdict


# Base Device Class (Template)
class Device(abc.ABC):
    def __init__(self, device_id, name, energy_usage=0):
        # Initialize device attributes
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

    # Control methods
    def turn_on(self):
        self.__status = 'on'

    def turn_off(self):
        self.__status = 'off'

    def get_energy_usage(self):
        return self.__energy_usage

    def __str__(self):
        return f"Device ID: {self.__device_id}, Name: {self.__name}, Status: {self.__status}, Energy Usage: {self.__energy_usage} kWh"


# Subclasses for devices
class Light(Device):
    def __init__(self, device_id, name, brightness=100):
        super().__init__(device_id, name, energy_usage=0.1 * (brightness / 100))
        self.__brightness = brightness


class Thermostat(Device):
    def __init__(self, device_id, name, temperature=22):
        super().__init__(device_id, name, energy_usage=0.5)
        self.__temperature = temperature


class Camera(Device):
    def __init__(self, device_id, name, resolution='1080p'):
        if resolution == '1080p':
            energy = 0.2
        elif resolution == '720p':
            energy = 0.1
        else:
            energy = 0.3
        super().__init__(device_id, name, energy_usage=energy)
        self.__resolution = resolution


# Device Controller
class DeviceController:
    def __init__(self):
        self.devices = {}

    def add_device(self, device):
        self.devices[device.get_id()] = device

    def remove_device(self, device_id):
        if device_id in self.devices:
            del self.devices[device_id]

    def list_devices(self):
        return list(self.devices.values())

    def execute_command(self, device_id, command):
        if device_id in self.devices:
            device = self.devices[device_id]
            if command == 'turn_on':
                device.turn_on()
            elif command == 'turn_off':
                device.turn_off()


# Smart Home Hub (Singleton)
class SmartHomeHub:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SmartHomeHub, cls).__new__(cls)
            cls._instance.controller = DeviceController()
            cls._instance.scheduled_tasks = []
        return cls._instance

    def schedule_task(self, device_id, command, time):
        self.scheduled_tasks.append((device_id, command, time))

    def display_status(self):
        devices = self.controller.list_devices()
        for device in devices:
            print(device)

    def total_energy_usage(self):
        total = 0
        devices = self.controller.list_devices()
        for device in devices:
            if device.get_status() == 'on':
                total += device.get_energy_usage()
        return total


# Main Execution (Template)
if __name__ == "__main__":
    hub = SmartHomeHub()

    # Add devices
    light = Light(1, "Living Room Light", 80)
    thermostat = Thermostat(2, "Bedroom Thermostat", 24)
    camera = Camera(3, "Front Door Camera", '1080p')

    hub.controller.add_device(light)
    hub.controller.add_device(thermostat)
    hub.controller.add_device(camera)

    # Display devices
    hub.display_status()

    # Execute commands
    hub.controller.execute_command(1, 'turn_on')
    hub.controller.execute_command(2, 'turn_on')

    # Schedule tasks
    hub.schedule_task(3, 'turn_on', datetime(2025, 3, 16, 12, 0))

    # Calculate and print total energy usage
    print(f"Total Energy Usage: {hub.total_energy_usage()} kWh")
