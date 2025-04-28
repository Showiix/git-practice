import abc
from flask import Flask, request, jsonify
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns

#database

def init_db():
    try:
        conn = sqlite3.connect('xjy_smarthome.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS devices(
               device_id TEXT PRIMARY KEY, -- 设备id
               name TEXT,  -- 设备名
               status TEXT,  -- 设备状态
               energy_usage REAL,  -- 设备能量消耗
               device_type TEXT, -- 设备类型
               brightness INTEGER,  -- 灯的亮度
               temperature INTEGER,  -- 温度
               resolution TEXT -- 摄像头的分辨率
    )''')
        conn.commit()
    
    except sqlite3.Error as e:
        print(f"数据库初始化出错： {e}")
    
    finally:
        conn.close()

# 插入或替换设备信息函数
def insert_or_replace_device(device_id, name, status, energy_usage, device_type, **kwargs):
    
    try:
        conn = sqlite3.connect('xjy_smarthome.db')
        c = conn.cursor()
        if device_type == 'light':
            brightness = kwargs.get('brightness')
            c.execute('''
                  INSERT OR REPLACE INTO devices

                  (device_id, name, status,energy_usage, device_type, brightness)

                  VALUES (?,?,?,?,?,?)
                ''',
                (device_id, name, status, energy_usage, 'light', brightness))
        elif device_type == 'camera':
            resolution = kwargs.get('resolution')
            c.execute('''
                  INSERT OR REPLACE INTO devices
                  (device_id, name, status, energy_usage, device_type, resolution)
                  VALUES (?,?,?,?,?,?)
                ''',
                (device_id, name, status, energy_usage, 'camera', resolution))
        elif device_type == 'thermostat':
            temperature = kwargs.get('temperature')
            c.execute('''
                  INSERT OR REPLACE INTO devices
                  (device_id, name, status, energy_usage, device_type, temperature)
                  VALUES (?,?,?,?,?,?)
                ''',
                (device_id, name, status, energy_usage, 'thermostat', temperature))
    except sqlite3.Error as e:
        print(f"数据库插入或替换出错： {e}")
    
    finally:
        if conn:
            conn.commit()
            conn.close()
        
            
            
    
    
    
    
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

    def update_db(self):
        try:
            conn = sqlite3.connect('xjy_smarthome.db')
            c = conn.cursor()
            c.execute('''
                  
                  UPDATE devices SET
                  status = ?,
                  energy_usage = ?
                  WHERE device_id = ?
                ''',
                (self.__status, self.__energy_usage, self.__device_id)
                
                )
            conn.commit()
        
        except sqlite3.Error as e:
            print(f"数据库更新出错： {e}")
            
        finally:
            if conn:
                conn.close()
            
   
                  
# Subclasses
class Light(Device):
    def __init__(self, device_id, name, brightness=100):
        super().__init__(device_id, name)
        self.__brightness = brightness
        self.save_db('light', brightness = brightness)
    
    def save_db(self,device_type, **kwargs):
        insert_or_replace_device(self.get_id(), self.get_name(), self.get_status(), self.get_energy_usage(), device_type, **kwargs)
                       
                  
class Thermostat(Device):
    def __init__(self, device_id, name, temperature=22):
        super().__init__(device_id, name)
        self.__temperature = temperature
        self.save_db('thermostat', temperature=temperature)
        
    def save_db(self, device_type, **kwargs):
        insert_or_replace_device(self.get_id(), self.get_name(), self.get_status(), self.get_energy_usage(), device_type, **kwargs)
        
        
class Camera(Device):
    def __init__(self, device_id, name, resolution='1080p'):
        super().__init__(device_id, name)
        self.__resolution = resolution
        self.save_db('camera', resolution = resolution)
        
    def save_db(self, device_type, **kwargs):
        insert_or_replace_device(self.get_id(), self.get_name(), self.get_status(), self.get_energy_usage(), device_type, **kwargs)
        
        
# Device Controller
class DeviceController:
    def __init__(self):
        self.devices = {}
    
    def load_devices_database(self):
        try:
            conn = sqlite3.connect('xjy_smarthome.db')
            c = conn.cursor()
            c.execute('SELECT * FROM devices')
            rows = c.fetchall()
        
            devices_classes = {
            'light': Light,
            'thermostat': Thermostat,
            'camera': Camera
            }
        
            for x in rows:
                device_id, name, status, energy_usage, device_type, brightness, temperature, resolution  = x
                kwargs = {}
                if device_type == 'light':
                    kwargs['brightness'] = brightness
                elif device_type == 'thermostat':
                    kwargs['temperature'] = temperature
                elif device_type == 'camera':
                    kwargs['resolution'] = resolution
                
                device = devices_classes[device_type](device_id, name, **kwargs)
                device._Device__status = status
                device._Device__energy_usage = energy_usage
                self.devices[device_id] = device
                device.update_db()
        
        except sqlite3.Error as e:
            print(f"数据库加载出错： {e}")

        finally:
            if conn:
                conn.close()
            
    
            
        
           
            
         

    def add_device(self, device):
        device_id = device.get_id()
        if device_id not in self.devices:
            self.devices[device_id] = device
        else:
            print(f"Device {device_id} 已经存在")

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
            cls._instance.controller.load_devices_database()
        return cls._instance

    def schedule_task(self, device_id, command, time):
        print(f"Task scheduled: {command} {device_id} at {time}")

    def display_status(self):
        return self.controller.list_devices()

    def total_energy_usage(self):
        return sum(device.get_energy_usage() for device in self.controller.devices.values())

app = Flask(__name__)
xjy_hub = SmartHomeHub()


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
    
#从数据库提取设备信息数据
def get_energy_usage_data():
    try:
        conn = sqlite3.connect('xjy_smarthome.db')
        c = conn.cursor()
        c.execute('SELECT name, energy_usage FROM devices')
        rows = c.fetchall()
        names = [row[0] for row in rows]
        energy_usages = [row[1] for row in rows]
        return names, energy_usages
    except sqlite3.Error as e:
        print(f"数据库查询出错： {e}")
    finally:
        if conn:
            conn.close()
            

#将设备能量消耗数据可视化
def plot_energy_usage():
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    names, energy_usages = get_energy_usage_data()
    plt.figure(figsize=(10, 6))  # 设置图形大小
    sns.barplot(x=names, y=energy_usages) # 使用seaborn绘制柱状图
    plt.title('设备能耗柱状图') #标题
    plt.xlabel('设备名称') #x轴名称
    plt.ylabel('能耗 (kWh)') #y轴名称
    plt.xticks(rotation=45) 
    plt.tight_layout() # 
    plt.show() 

    
    

    
    
    
    
    
    
    

if __name__ == "__main__":
    init_db()
    insert_or_replace_device('L1', '一号灯', 'off', 0.1, 'light', brightness=80)
    insert_or_replace_device('L2', '二号灯', 'off', 0.2, 'light', brightness=80)
    insert_or_replace_device('L3', '三号灯', 'off', 0.3, 'light', brightness=80)
    insert_or_replace_device('C1', '一号相机', 'off', 0.4, 'camera', resolution='960')
    insert_or_replace_device('C2', '二号相机', 'off', 0.5, 'camera', resolution='2560')
    insert_or_replace_device('C3', '三号相机', 'off', 0.6, 'camera', resolution='1080')
    insert_or_replace_device('T1', '一号温控器', 'off', 0.7, 'thermostat', temperature=20)
    insert_or_replace_device('T2', '二号温控器', 'off', 0.8, 'thermostat', temperature=30)
    insert_or_replace_device('T3', '三号温控器', 'off', 0.9, 'thermostat', temperature=40)
    
    plot_energy_usage() #调用函数回执图标
    app.run(debug=True)
    
