![netpalm_log](/images/netpalm.png)

## why netpalm?

netpalm is a ReST API into your dusty old network devices, netpalm makes it easy to push and pull network state from your apps. netpalm can abstract and render structured data both inbound and outbound to your network devices native telnet, SSH, NETCONF or RESTCONF interface.
netpalm leverages popular [napalm](https://github.com/napalm-automation/napalm), [netmiko](https://github.com/ktbyers/netmiko),  ncclient and requests library's for network device communication, these powerful libs supprt a vast number of vendors and OS

## netpalm features

- Speaks ReST & JSON to your app and CLI/NETCONF/RESTCONF to your network devices
- Provides a multi-level abstraction interface for service modeling of Create, Retrieve, Delete methods
- Ability to write your own [service templates](https://github.com/tbotnz/netpalm/blob/master/backend/plugins/service_templates/vlan_service.j2)
- Per device async task queuing (Ensure you dont overload your VTY's) or Pooled async processes
- Large amount of supported multivendor devices ( cheers to the netmiko & napalm & ncclient lads )
- Supports TextFSM for parsing/structuring device data (includes [ntc-templates](https://github.com/networktocode/ntc-templates))
- Supports Jinja2 for model driven deployments of config onto devices accross [napalm](https://github.com/napalm-automation/napalm), [netmiko](https://github.com/ktbyers/netmiko) and ncclient
- Supports automated download and installation of TextFSM templates from http://textfsm.nornir.tech online TextFSM development tool
- Can be used to execute any python script async via the ReST API and includes passing in of parameters
- Task oriented asynchronous parallel processing
- Supports on the fly changes to async queue strategy for a device
- OpenAPI / SwaggerUI docs inbuilt via the default / route
- Includes large postman collection of examples
- Horizontal scale out architecture supported by each component
- Automatically generates a JSON schema for any Jinja2 Template
- Can render NETCONF XML responses into JSON on the fly
- Can render Jinja2 templates only if required via the API

## concepts

netpalm acts as a ReST broker for NAPALM, Netmiko, NCCLIENT or a Python Script.
It uses TextFSM or Jinja2 to model and transform both ingress and egress data if required.
You make an API call to netpalm and it will establish a queue to your device and start sending configuration

![netpalm concept](/images/arch.png)

## using netpalm examples

### getconfig method

![netpalm eg1](/images/netpalm_eg_1.png)

#### check response

![netpalm eg2](/images/netpalm_eg_2.png)

### getconfig method with textfsm arg

netpalm also supports all arguments for the transport libs, simply pass them in as below

![netpalm eg3](/images/netpalm_eg_3.png)

#### check response

![netpalm eg4](/images/netpalm_eg_4.png)

### rapid template development and deployment

netpalm is integrated into http://textfsm.nornir.tech so you can ingest your templates with ease

![netpalm auto ingest](/images/netpalm_ingest.gif)

### API documentation

netpalm comes with a [postman collection](https://documenter.getpostman.com/view/2391814/SzYbxcQx?version=latest) and an OpenAPI based API with swagger ui
![netpalm swagger](/images/oapi.png)

## container installation

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
sudo docker-compose up -d --build
```

import the postman collection, set the ip addresses to that of your docker host and off you go (default netpalm port is 9000)
```
http://$(yourdockerhost):9000
```

## scaling
netpalm containers can be scaled out/in as required, define how many containers are required of each type
```
docker-compose scale netpalm-controller=1 netpalm-worker-pinned=2 netpalm-worker-fifo=3
```

#### configuring netpalm

edit the config.json file too set params as required
```
{
    "api_key": "2a84465a-cf38-46b2-9d86-b84Q7d57f288",
    "api_key_name" : "x-api-key",
    "cookie_domain" : "netpalm.local",
    "listen_port": 9000,
    "listen_ip":"0.0.0.0",
    "gunicorn_workers":3,
    "redis_task_ttl":500,
    "redis_task_timeout":500,
    "redis_server":"redis",
    "redis_port":6379,
    "redis_core_q":"process",
    "redis_fifo_q":"fifo",
    "redis_queue_store":"netpalm_queue_store",
    "pinned_process_per_node":100,
    "fifo_process_per_node":10,
    "txtfsm_index_file":"backend/plugins/ntc-templates/index",
    "txtfsm_template_server":"http://textfsm.nornir.tech",
    "custom_scripts":"backend/plugins/custom_scripts/",
    "jinja2_config_templates":"backend/plugins/jinja2_templates/",
    "jinja2_service_templates":"backend/plugins/service_templates/",
    "self_api_call_timeout":15
}
```

### useful netpalm resources

netpalm getting started blog:
- [netpalm Intro Part 1](https://blog.wimwauters.com/networkprogrammability/2020-04-14_netpalm_introduction_part1/)
- [netpalm Intro Part 2](https://blog.wimwauters.com/networkprogrammability/2020-04-15_netpalm_introduction_part2/)
- [netpalm Intro Part 3](https://blog.wimwauters.com/networkprogrammability/2020-04-17_netpalm_introduction_part3/)

### netpalm slack channel

#netpalm on networktocode.slack.com

### license

All code belongs to that of its respective owners
