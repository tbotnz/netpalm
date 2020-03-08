# NetPalm

Why NetPalm?
Netpalm is a ReST API into your dusty old network devices, NetPalm makes it easy to push and pull network state from your web apps.
NetPalm leverages popular [napalm](https://github.com/napalm-automation/napalm) and [netmiko](https://github.com/ktbyers/netmiko) library's for network device communication, these powerful libs supprt a vast number of vendors and OS

## Netpalm Features

- Asynchronous parallel processing
- Task oriented
- Per device configuration queuing (Ensure you dont overload your VTY's)
- Standard ReST interface
- Large amount of supported multivendor devices ( cheers to the netmiko & napalm lads )
- Included postman collection of examples
- TextFSM support via netmiko
- Supports rapid TextFSM development and deployment via integration into http://textfsm.nornir.techdeployment 

## Using Netpalm

### Code
All of the code you need is located in this repo. Clone the repo and access it with the following commands:
```
git clone https://github.com/tbotnz/netpalm
cd netpalm
```

#### Concepts
Netpalm acts as a ReST broker for NAPALM and Netmiko.
You make an API call to netpalm and it will establish a queue to your device and start sending configuration
![netpalm concept](/images/netpalm_concept.png)

#### Get config from a network device
Post some config to the getconfig route

### Postman example
getconfig method
![netpalm eg1](/images/netpalm_eg_1.png)

check response
![netpalm eg2](/images/netpalm_eg_2.png)

#### Get config from a network device using the librarys arg
netpalm also supports all arguments for the transport libs, simply pass them in as below
![netpalm eg3](/images/netpalm_eg_3.png)

check response
![netpalm eg4](/images/netpalm_eg_4.png)

#### Rapid template development and deployment
netpalm is integrated into http://textfsm.nornir.tech so you can ingest your templates with ease
![netpalm auto ingest](/images/netpalm_ingest.gif)

#### Postman Collection
netpalm comes bundled with a postman collection to make it easy to get going
![netpalm postman](/images/netpalm_postman.png)

### Configuring Netpalm
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
    "redis_core_q":"process"
}
```

### Container Installation
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

## Netpalm slack channel
#netpalm on networktocode.slack.com

## License
All code belongs to that of its respective owners
