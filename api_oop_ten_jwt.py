import abc
from flask import Flask, request, jsonify
import sqlite3
from sqlite3 import Error
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta
import jwt
from flask import make_response

# 配置日志
logging.basicConfig(level=logging.ERROR, filename='app.log', format='%(asctime)s - %(levelname)s - %(message)s')

# 初始化数据库
db_name = 'xjy_smarthome.db'

# 数据库连接上下文管理器
@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        yield conn
    except Error as e:
        logging.error(f"数据库连接出错： {e}")
    finally:
        if conn:
            conn.close()


def init_db():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            # 创建主设备表
            c.execute('''CREATE TABLE IF NOT EXISTS devices(
                   device_id TEXT PRIMARY KEY, -- 设备id
                   name TEXT,  -- 设备名
                   status TEXT,  -- 设备状态
                   energy_usage REAL,  -- 设备能量消耗
                   device_type TEXT -- 设备类型
                )''')
            # 创建灯光属性表
            c.execute('''CREATE TABLE IF NOT EXISTS light_attributes(
                   device_id TEXT PRIMARY KEY,
                   brightness INTEGER,
                   FOREIGN KEY (device_id) REFERENCES devices(device_id)
                )''')
            # 创建恒温器属性表
            c.execute('''CREATE TABLE IF NOT EXISTS thermostat_attributes(
                   device_id TEXT PRIMARY KEY,
                   temperature INTEGER,
                   FOREIGN KEY (device_id) REFERENCES devices(device_id)
                )''')
            # 创建摄像头属性表
            c.execute('''CREATE TABLE IF NOT EXISTS camera_attributes(
                   device_id TEXT PRIMARY KEY,
                   resolution TEXT,
                   FOREIGN KEY (device_id) REFERENCES devices(device_id)
                )''')
            # 创建用户表
            c.execute('''CREATE TABLE IF NOT EXISTS users(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT UNIQUE,
                   password TEXT
                )''')
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"数据库初始化出错： {e}")


# 备份数据库函数
def backup_database(backup_file=None):
    if backup_file is None:
        backup_file = f'backup_{datetime.now().strftime("%Y%m%d%H%M%S")}.db'
    try:
        src_conn = sqlite3.connect(db_name)
        dest_conn = sqlite3.connect(backup_file)
        with dest_conn:
            src_conn.backup(dest_conn)
        src_conn.close()
        dest_conn.close()
    except Exception as e:
        logging.error(f"数据库备份出错： {e}")


# 插入或替换设备信息
def insert_or_replace_device(device_id, name, status, energy_usage, device_type, **kwargs):
    with get_db_connection() as conn:
        c = conn.cursor()
        # 插入或替换主设备表信息
        c.execute('''
            INSERT OR REPLACE INTO devices (device_id, name, status, energy_usage, device_type)
            VALUES (?,?,?,?,?)
        ''', (device_id, name, status, energy_usage, device_type))
        if device_type == 'light':
            brightness = kwargs.get('brightness')
            c.execute('''
                INSERT OR REPLACE INTO light_attributes (device_id, brightness)
                VALUES (?,?)
            ''', (device_id, brightness))
        elif device_type == 'thermostat':
            temperature = kwargs.get('temperature')
            c.execute('''
                INSERT OR REPLACE INTO thermostat_attributes (device_id, temperature)
                VALUES (?,?)
            ''', (device_id, temperature))
        elif device_type == 'camera':
            resolution = kwargs.get('resolution')
            c.execute('''
                INSERT OR REPLACE INTO camera_attributes (device_id, resolution)
                VALUES (?,?)
            ''', (device_id, resolution))
        conn.commit()


# 设备基类
class Device(abc.ABC):
    def __init__(self, device_id, name, energy_usage=0):
        self.__device_id = device_id
        self.__name = name
        self.__status = 'off'
        self.__energy_usage = energy_usage

    # 获取方法
    def get_id(self):
        return self.__device_id

    def get_name(self):
        return self.__name

    def get_status(self):
        return self.__status

    def get_energy_usage(self):
        return self.__energy_usage

    # 控制方法
    def turn_on(self):
        if self.__status != 'on':
            self.__status = 'on'
            self.__energy_usage += 0.1
            self.update_db()

    def turn_off(self):
        if self.__status != 'off':
            self.__status = 'off'
            self.__energy_usage += 0.02
            self.update_db()

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
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    UPDATE devices SET
                    status = ?,
                    energy_usage = ?
                    WHERE device_id = ?
                ''', (self.__status, self.__energy_usage, self.__device_id))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"数据库更新出错： {e}")


# 子类
class Light(Device):
    def __init__(self, device_id, name, brightness=100):
        super().__init__(device_id, name)
        self.__brightness = brightness
        self.save_db('light', brightness=brightness)

    def save_db(self, device_type, **kwargs):
        insert_or_replace_device(self.get_id(), self.get_name(), self.get_status(), self.get_energy_usage(), device_type,
                                 **kwargs)


class Thermostat(Device):
    def __init__(self, device_id, name, temperature=22):
        super().__init__(device_id, name)
        self.__temperature = temperature
        self.save_db('thermostat', temperature=temperature)

    def save_db(self, device_type, **kwargs):
        insert_or_replace_device(self.get_id(), self.get_name(), self.get_status(), self.get_energy_usage(), device_type,
                                 **kwargs)


class Camera(Device):
    def __init__(self, device_id, name, resolution='1080p'):
        super().__init__(device_id, name)
        self.__resolution = resolution
        self.save_db('camera', resolution=resolution)

    def save_db(self, device_type, **kwargs):
        insert_or_replace_device(self.get_id(), self.get_name(), self.get_status(), self.get_energy_usage(), device_type,
                                 **kwargs)


# 设备控制类
class DeviceController:
    def __init__(self):
        self.devices = {}

    def load_devices_database(self):
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute('SELECT * FROM devices')
                rows = c.fetchall()

                devices_classes = {
                    'light': Light,
                    'thermostat': Thermostat,
                    'camera': Camera
                }

                for x in rows:
                    device_id, name, status, energy_usage, device_type = x
                    kwargs = {}
                    if device_type == 'light':
                        c.execute('SELECT brightness FROM light_attributes WHERE device_id = ?', (device_id,))
                        result = c.fetchone()
                        if result:
                            kwargs['brightness'] = result[0]
                    elif device_type == 'thermostat':
                        c.execute('SELECT temperature FROM thermostat_attributes WHERE device_id = ?', (device_id,))
                        result = c.fetchone()
                        if result:
                            kwargs['temperature'] = result[0]
                    elif device_type == 'camera':
                        c.execute('SELECT resolution FROM camera_attributes WHERE device_id = ?', (device_id,))
                        result = c.fetchone()
                        if result:
                            kwargs['resolution'] = result[0]

                    device = devices_classes[device_type](device_id, name, **kwargs)
                    # 使用公共方法设置状态和能量消耗
                    if status == 'on':
                        device.turn_on()
                    else:
                        device.turn_off()
                    device._Device__energy_usage = energy_usage
                    self.devices[device_id] = device
                    device.update_db()
        except sqlite3.Error as e:
            logging.error(f"数据库加载出错： {e}")

    def add_device(self, device):
        device_id = device.get_id()
        if device_id not in self.devices:
            self.devices[device_id] = device
        else:
            logging.warning(f"Device {device_id} 已经存在")

    def remove_device(self, device_id):
        if device_id in self.devices:
            del self.devices[device_id]
            try:
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute('DELETE FROM devices WHERE device_id = ?', (device_id,))
                    c.execute('DELETE FROM light_attributes WHERE device_id = ?', (device_id,))
                    c.execute('DELETE FROM thermostat_attributes WHERE device_id = ?', (device_id,))
                    c.execute('DELETE FROM camera_attributes WHERE device_id = ?', (device_id,))
                    conn.commit()
                return True
            except sqlite3.Error as e:
                logging.error(f"数据库删除出错： {e}")
                return False
        return False

    def list_devices(self):
        devices_info = []
        for device in self.devices.values():
            device_dict = device.change_to_dict()
            device_type = None
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute('SELECT device_type FROM devices WHERE device_id = ?', (device.get_id(),))
                result = c.fetchone()
                if result:
                    device_type = result[0]
            if device_type == 'light':
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute('SELECT brightness FROM light_attributes WHERE device_id = ?', (device.get_id(),))
                    result = c.fetchone()
                    if result:
                        device_dict['brightness'] = result[0]
            elif device_type == 'thermostat':
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute('SELECT temperature FROM thermostat_attributes WHERE device_id = ?', (device.get_id(),))
                    result = c.fetchone()
                    if result:
                        device_dict['temperature'] = result[0]
            elif device_type == 'camera':
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute('SELECT resolution FROM camera_attributes WHERE device_id = ?', (device.get_id(),))
                    result = c.fetchone()
                    if result:
                        device_dict['resolution'] = result[0]
            devices_info.append(device_dict)
        return devices_info

    def execute_command(self, device_id, command):
        device = self.devices.get(device_id)
        if device:
            if command == 'on':
                device.turn_on()
                logging.info(f"Executed {command} on {device.get_name()}")
                return True
            elif command == 'off':
                device.turn_off()
                logging.info(f"Executed {command} on {device.get_name()}")
                return True
            else:
                logging.warning(f"Invalid command: {command}")
                return False
        else:
            logging.warning(f"Device {device_id} not found")
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
        logging.info(f"Task scheduled: {command} {device_id} at {time}")

    def display_status(self):
        return self.controller.list_devices()

    def total_energy_usage(self):
        return sum(device.get_energy_usage() for device in self.controller.devices.values())


app = Flask(__name__)
xjy_hub = SmartHomeHub()

# 密钥，用于JWT签名和验证
SECRET_KEY = "a_showiix_showiix_showiix_showiix_1234567890abcdef"

# 注册用户函数
def register_user(username, password):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('INSERT INTO users (username, password) VALUES (?,?)', (username, password))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        logging.error(f"用户 {username} 已存在")
        return False
    except sqlite3.Error as e:
        logging.error(f"注册用户时出错： {e}")
        return False


# 登录接口，生成JWT
@app.route('/login', methods=['POST'])
def login():
    # 从数据库验证用户信息
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT password FROM users WHERE username = ?', (username,))
            result = c.fetchone()
            if result:
                stored_password = result[0]
                if stored_password == password:
                    # 生成JWT
                    payload = {
                        'user': username,
                        'exp': datetime.utcnow() + timedelta(minutes=30)
                    }
                    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
                    return jsonify({'token': token})
    except sqlite3.Error as e:
        logging.error(f"登录时查询数据库出错： {e}")

    return jsonify({'error': 'Invalid credentials'}), 401


# JWT验证装饰器
def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing!'}), 401
        try:
            token = token.replace('Bearer ', '')
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 401
        return f(*args, **kwargs)
    return decorated


# api 1
@app.route('/devices', methods=['GET'], endpoint='get_devices')
@token_required
def get_devices():
    devices = xjy_hub.display_status()
    return jsonify(devices)


# api 2
@app.route('/devices/<device_id>', methods=['GET'], endpoint='get_device')
@token_required
def get_device(device_id):
    device = xjy_hub.controller.devices.get(device_id)
    if device:
        device_dict = device.change_to_dict()
        device_type = None
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT device_type FROM devices WHERE device_id = ?', (device.get_id(),))
            result = c.fetchone()
            if result:
                device_type = result[0]
        if device_type == 'light':
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute('SELECT brightness FROM light_attributes WHERE device_id = ?', (device.get_id(),))
                result = c.fetchone()
                if result:
                    device_dict['brightness'] = result[0]
        elif device_type == 'thermostat':
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute('SELECT temperature FROM thermostat_attributes WHERE device_id = ?', (device.get_id(),))
                result = c.fetchone()
                if result:
                    device_dict['temperature'] = result[0]
        elif device_type == 'camera':
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute('SELECT resolution FROM camera_attributes WHERE device_id = ?', (device.get_id(),))
                result = c.fetchone()
                if result:
                    device_dict['resolution'] = result[0]
        return jsonify(device_dict)
    else:
        return jsonify({'error': f"设备{device_id}不存在"}), 404


# api 3
@app.route('/devices/<device_id>/<command>', methods=['POST'], endpoint='execute_command')
@token_required
def execute_command(device_id, command):
    result = xjy_hub.controller.execute_command(device_id, command)
    return jsonify({'message': f"命令{command}已发送给设备{device_id},结果为{result}"})


# api 4
@app.route('/energy_usage', methods=['GET'], endpoint='get_total_energy_usage')
@token_required
def get_total_energy_usage():
    total_energy_usage = xjy_hub.total_energy_usage()
    return jsonify({'total_energy_usage': total_energy_usage})


# api 5
@app.route('/devices', methods=['POST'], endpoint='add_device')
@token_required
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


# api 6
@app.route('/devices/<device_id>', methods=['DELETE'], endpoint='delete_device')
@token_required
def delete_device(device_id):
    result = xjy_hub.controller.remove_device(device_id)
    if result:
        return jsonify({'message': f"设备{device_id}已删除"}), 200
    else:
        return jsonify({'error': f"设备{device_id}不存在或删除失败"}), 404


if __name__ == "__main__":
    init_db()
    
    users_to_register = [
        ('showiix', 'aa1312134353'),
        ('showiix2', 'aa1312134353'),
        ('showiix3', 'aa1312134353'),
        ('showiix4', 'aa1312134353'),
        ('showiix5', 'aa1312134353')
    ]

    for username, password in users_to_register:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE username = ?', (username,))
            result = c.fetchone()
            if not result:
                register_user(username, password)
                
    insert_or_replace_device('L1', '一号灯', 'off', 0.1, 'light', brightness=80)
    insert_or_replace_device('L2', '二号灯', 'off', 0.2, 'light', brightness=80)
    insert_or_replace_device('L3', '三号灯', 'off', 0.3, 'light', brightness=80)
    insert_or_replace_device('C1', '一号相机', 'off', 0.4, 'camera', resolution='960')
    insert_or_replace_device('C2', '二号相机', 'off', 0.5, 'camera', resolution='2560')
    insert_or_replace_device('C3', '三号相机', 'off', 0.6, 'camera', resolution='1080')
    insert_or_replace_device('T1', '一号温控器', 'off', 0.7, 'thermostat', temperature=20)
    insert_or_replace_device('T2', '二号温控器', 'off', 0.8, 'thermostat', temperature=30)
    insert_or_replace_device('T3', '三号温控器', 'off', 0.9, 'thermostat', temperature=40)

    app.run(debug=True)
    