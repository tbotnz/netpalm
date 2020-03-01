from netmiko import ConnectHandler

class netmko:

    def __init__(self, **kwargs):
        self.username = kwargs.get('username', False)
        self.password = kwargs.get('password', False)
        self.driver = kwargs.get('driver', False)
        self.host = kwargs.get('host', False)
    
    def connect(self):
        try:
            netmikoses = ConnectHandler(device_type=self.driver, host=self.host, username=self.username, password=self.password)
            return netmikoses
        except Exception as e:
            return e

    def sendcommand(self, session=False, command=False):
        try:
            result = {}
            for commands in command:
                response = session.send_command(commands)
                if response:
                    result[commands] = response.split('\n')
            return result
        except Exception as e:
            return e

    def config(self, session=False, command=False):
        try:
            response = session.send_config_set(command)
            result = {}
            result["changes"] = response.split('\n')
            return result
        except Exception as e:
            return e

    def logout(self, session):
        try:
            response = session.disconnect()
            return response
        except Exception as e:
            return e