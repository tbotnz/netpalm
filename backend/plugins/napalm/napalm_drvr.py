import napalm

class naplm:

    def __init__(self, **kwargs):
        self.username = kwargs.get('username', False)
        self.password = kwargs.get('password', False)
        self.driver = kwargs.get('driver', False)
        self.host = kwargs.get('host', False)
        self.kwarg = kwargs.get('args', False)
        
    def connect(self):
        try:
            driver = napalm.get_network_driver(self.driver)
            if self.kwarg:
                napalmses = driver(hostname=self.host, username=self.username, password=self.password, optional_args=self.kwarg)
            else:
                napalmses = driver(hostname=self.host, username=self.username, password=self.password)
            napalmses = driver(hostname=self.host, username=self.username, password=self.password)
            return napalmses
        except Exception as e:
            return str(e)

    def sendcommand(self, session=False, command=False):
        try:
            session.open()
            response = session.cli(command)
            result = {}
            for command in response:
                result[command] = response[command].split('\n')
            return result
        except Exception as e:
            return str(e)

    def config(self, session=False, command=False):
        try:
            #normalise config for napalm
            napalmconfig = "\n".join(command[0:])
            session.open()
            session.load_merge_candidate(config=napalmconfig)
            diff = session.compare_config()
            response = session.commit_config()
            result = {}
            result["changes"] = diff.split('\n')
            return result
        except Exception as e:
            return str(e)

    def logout(self, session):
        try:
            response = session.close()
            return response
        except Exception as e:
            return str(e)
