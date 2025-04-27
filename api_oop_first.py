import abc
from collections import defaultdict
from flask import Flask, request, jsonify

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

    def change_to_dict(self):
        return {
            'device_id': self.get_id(),
            'name': self.get_name(),
            'status': self.get_status(),
            'energy_usage': self.get_energy_usage()
        }

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
        return [device.change_to_dict() for device in self.devices.values()]

    def execute_command(self, device_id, command):
        device = self.devices.get(device_id)
        if device:
            if command == 'on':
                device.turn_on()
                print(f"Executed {command} on {device.get_name()}")
                return True
            elif command == 'off':
                device.turn_off()
                print(f"Executed {command} on {device.get_name()}")
                return True
            else:
                print(f"Invalid command: {command}")
                return False
        else:
            print(f"Device {device_id} not found")
            return False

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
        return self.controller.list_devices()

    def total_energy_usage(self):
        return sum(device.get_energy_usage() for device in self.controller.devices.values())

app = Flask(__name__)
xjy_hub = SmartHomeHub()

light = Light("L1", "Living Room Light")
thermostat = Thermostat("T1", "Home Thermostat")
camera = Camera("C1", "Front Door Camera")

# add devices to the controller
xjy_hub.controller.add_device(light)
xjy_hub.controller.add_device(thermostat)
xjy_hub.controller.add_device(camera)

#api 1
@app.route('/devices', methods=['GET'])
def get_devices():
    devices = xjy_hub.display_status()
    return jsonify(devices)

#api 2
@app.route('/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    device = xjy_hub.controller.devices.get(device_id)
    if device:
        return jsonify(device.change_to_dict())
    else:
        return jsonify({'error': f"设备{device_id}不存在"}), 404

#api 3
@app.route('/devices/<device_id>/<command>', methods=['POST'])
def execute_command(device_id, command):
    result = xjy_hub.controller.execute_command(device_id, command)
    return jsonify({'message': f"命令{command}已发送给设备{device_id},结果为{result}"})

#api 4
@app.route('/energy_usage', methods=['GET'])
def get_total_energy_usage():
    total_energy_usage = xjy_hub.total_energy_usage()
    return jsonify({'total_energy_usage': total_energy_usage})

#api 5
@app.route('/devices', methods=['POST'])
def add_device():
    data = request.get_json()
    device_id = data.get('id')
    device_name = data.get('name')
    device_type = data.get('type')

    device_classes = {
        'light': Light,
        'thermostat': Thermostat,
        'camera': Camera
    }

    if device_type in device_classes:
        kwargs = {}
        if device_type == 'light':
            kwargs['brightness'] = data.get('brightness', 100)
        elif device_type == 'thermostat':
            kwargs['temperature'] = data.get('temperature', 20)
        elif device_type == 'camera':
            kwargs['resolution'] = data.get('resolution', '1080p')

        device = device_classes[device_type](device_id, device_name, **kwargs)
        xjy_hub.controller.add_device(device)
        return jsonify({'message': f"设备{device_name}已添加到控制器"})
    else:
        return jsonify({'error': '不支持的设备类型'}), 400

#api 6
@app.route('/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    result = xjy_hub.controller.remove_device(device_id)
    if result:
        return jsonify({'message': f"设备{device_id}已删除"}), 200
    else:
        return jsonify({'error': f"设备{device_id}不存在"}), 404

if __name__ == "__main__":
    app.run(debug=True)