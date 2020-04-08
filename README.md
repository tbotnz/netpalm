![netpalm_log](/images/netpalm.png)

Why NetPalm?
Netpalm is a ReST API into your dusty old network devices, NetPalm makes it easy to push and pull network state from your web apps.
NetPalm leverages popular [napalm](https://github.com/napalm-automation/napalm), [netmiko](https://github.com/ktbyers/netmiko) and ncclient library's for network device communication, these powerful libs supprt a vast number of vendors and OS

## Netpalm Features

- Talks a Rest API to your app and CLI/NETCONF to your network devices
- Per device task queuing (Ensure you dont overload your VTY's)
- Large amount of supported multivendor devices ( cheers to the netmiko & napalm & ncclient lads )
- Supports TextFSM for parsing/structuring device data (includes [ntc-templates](https://github.com/networktocode/ntc-templates))
- Supports Jinja2 for model driven deployments of config onto devices accross [napalm](https://github.com/napalm-automation/napalm), [netmiko](https://github.com/ktbyers/netmiko) and ncclient
- Can be used to execute any python script via the ReST API and includes passing in of parameters
- Provides an abstraction interface for service modeling of Create, Retrieve, Delete methods for a service
- Includes large postman collection of examples
- Supports automated download and installation of TextFSM templates from http://textfsm.nornir.tech online TextFSM development tool
- Automatically generates a JSON schema for any Jinja2 Template
- Can render NETCONF XML responses into JSON on the fly
- Can render Jinja2 templates only if required via the API
- Normalised ReST interface
- Asynchronous parallel processing
- Task oriented

## Concepts

Netpalm acts as a ReST broker for NAPALM, Netmiko, NCCLIENT or a Python Script.
It uses TextFSM or Jinja2 to model and transform both ingress and egress data if required.
You make an API call to netpalm and it will establish a queue to your device and start sending configuration

![netpalm concept](/images/arch.png)

## Using Netpalm

### API catalog
[Please view the API docs here](https://documenter.getpostman.com/view/2391814/SzYbxcQx?version=latest)

### Postman example - getconfig method
![netpalm eg1](/images/netpalm_eg_1.png)

#### check response

![netpalm eg2](/images/netpalm_eg_2.png)

### Postman example - getconfig method with textfsm arg

netpalm also supports all arguments for the transport libs, simply pass them in as below

![netpalm eg3](/images/netpalm_eg_3.png)

#### check response

![netpalm eg4](/images/netpalm_eg_4.png)

### Rapid template development and deployment

netpalm is integrated into http://textfsm.nornir.tech so you can ingest your templates with ease

![netpalm auto ingest](/images/netpalm_ingest.gif)

### Included Postman Collection

netpalm comes bundled with a postman collection to make it easy to get going

![netpalm postman](/images/netpalm_postman.png)

## Container Installation

ensure you first have docker installed
```
sudo apt-get install docker.io
sudo apt-get install docker-compose
```

clone in netpalm
```
git clone https://github.com/tbotnz/netpalm.git
cd netpalm
```

build container
```
sudo docker build -t netpalm .
sudo docker-compose up -d
```

import the postman collection, set the ip addresses to that of your docker host and off you go (default netpalm port is 9000)
```
http://$(yourdockerhost):9000
```


#### Configuring Netpalm

edit the config.json file too set params as required
```
{
    "apikey": "2a84465a-cf38-46b2-9d86-b84Q7d57f288",
    "listen_port": 9000,
    "listen_ip":"0.0.0.0",
    "redis_task_ttl":500,
    "redis_task_timeout":500,
    "redis_server":"redis",
    "redis_port":6379,
    "redis_core_q":"process",
    "txtfsm_index_file":"backend/plugins/ntc-templates/index",
    "txtfsm_template_server":"http://textfsm.nornir.tech",
    "custom_scripts":"backend/plugins/custom_scripts/",
    "jinja2_templates":"backend/plugins/jinja2_templates/"
}
```

### Netpalm slack channel

#netpalm on networktocode.slack.com

### License

All code belongs to that of its respective owners
