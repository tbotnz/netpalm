![netpalm_log](/netpalm/static/images/netpalm.png)

## why netpalm?

netpalm is a ReST API into your dusty old network devices, netpalm makes it easy to push and pull network state from your apps. netpalm can abstract and render structured data both inbound and outbound to your network devices native telnet, SSH, NETCONF or RESTCONF interface.
netpalm leverages popular [napalm](https://github.com/napalm-automation/napalm), [netmiko](https://github.com/ktbyers/netmiko),  ncclient and requests library's for network device communication, these powerful libs supprt a vast number of vendors and OS

## netpalm features

- Speaks ReST & JSON to your app and CLI over SSH or Telnet or NETCONF/RESTCONF to your network devices
- Built in multi-level abstraction interface for service modeling of Create, Retrieve, Delete methods
- Ability to write your own [service models and templates](https://github.com/tbotnz/netpalm/tree/master/backend/plugins/extensibles/j2_service_templates) which are self documenting to Open API 3.0 when a model is used
- Supports pre and post checks accross CLI devices, config only deployed on pre check pass 
- Per device async task queuing (Ensure you dont overload your VTY's) or Pooled async processes
- Large amount of supported multivendor devices ( cheers to the netmiko & napalm & ncclient lads )
- TextFSM for parsing/structuring device data (includes [ntc-templates](https://github.com/networktocode/ntc-templates))
- Genie support for parsing device data
- Jinja2 for model driven deployments of config onto devices accross [napalm](https://github.com/napalm-automation/napalm), [netmiko](https://github.com/ktbyers/netmiko) and ncclient
- Automated download and installation of TextFSM templates from http://textfsm.nornir.tech online TextFSM development tool
- ReST based Webhook w/ args & the ability for you to BYO webhooks
- Execute ANY python script as async via the ReST API and includes passing in of parameters
- Supports on the fly changes to async queue strategy for a device ( either per device pinned queues or pooled queues )
- OpenAPI / SwaggerUI docs inbuilt via the default route
- Configurable caching meaning netpalm does not have to keep asking your device the things over and over again
- Large [online](https://documenter.getpostman.com/view/2391814/T1DqgwcU?version=latest#33acdbb8-b5cd-4b55-bc67-b15c328d6c20) postman collection of examples
- Horizontal container based scale out architecture supported by each component
- Automatically generates a JSON schema for any Jinja2 Template
- Can render NETCONF XML responses into JSON on the fly
- Can render Jinja2 templates only if required via the API

## concepts

netpalm acts as a ReST broker for NAPALM, Netmiko, NCCLIENT or a Python Script.
netpalm uses TextFSM or Jinja2 to model and transform both ingress and egress data if required.
You make an API call to netpalm and it will establish a queue to your device and start sending configuration

![netpalm concept](/netpalm/static/images/arch.png)

## basic netpalm example

Whilst we can show you examples for days we reccomend checking the online [postman collection](https://documenter.getpostman.com/view/2391814/T1DqgwcU?version=latest#33acdbb8-b5cd-4b55-bc67-b15c328d6c20) to get a feel for what can be done.
We also host a [public instance](https://netpalm.tech) have a look at the swagger ui

### getconfig method

netpalm also supports all arguments for the transport libs, simply pass them in as below

![netpalm eg3](/netpalm/static/images/netpalm_eg_3.png)

#### check response

![netpalm eg4](/netpalm/static/images/netpalm_eg_4.png)

### service templates in action

netpalm supports model driven service templates, these self render an OpenAPI 3 interface and provide abstraction and orchestration of tasks accross many devices using the get/setconfig or script methods.

The below example demonstrates basic SNMP state orchestration accross multiple devices for create, retrieve, delete 

![netpalm auto ingest](/netpalm/static/images/np_service.gif)

### rapid template development and deployment

netpalm is integrated into http://textfsm.nornir.tech so you can ingest your templates with ease

![netpalm auto ingest](/netpalm/static/images/netpalm_ingest.gif)

### API documentation

netpalm comes with a [postman collection](https://documenter.getpostman.com/view/2391814/T1DqgwcU?version=latest#33acdbb8-b5cd-4b55-bc67-b15c328d6c20) and an OpenAPI based API with swagger ui
![netpalm swagger](/netpalm/static/images/oapi.png)

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

## caching
* Supports the following per-request configuration (`/getconfig` routes only for now)
    * permit the result of this request to be cached (default: false), and permit this request to return cached data
    * hold the cache for 30 seconds (default: 300.  Should not be set above `redis_task_result_ttl` which defaults to 500)
    * do NOT invalidate any existing cache for this request (default: false)
    ```json
      {
        "cache": {
          "enabled": true,
          "ttl": 30,
          "poison": false
        }
      }
     ```
  
* Supports the following global configuration:
    * Enable/Disable caching: `"redis_cache_enabled": true`
        for caching to apply it must be enabled BOTH globally and in the request itself
    * Default TTL:  `"redis_cache_default_timeout": 300`

* Any change to the request payload will result in a new cache key EXCEPT:
    * JSON formatting.  `{ "x": 1, "y": 2 } == {"x":1,"y":2}`
    * Dictionary ordering:  `{"x":1,"y":2} == {"y":2,"x"1}`
    * changes to cache configuration (e.g. changing the TTL, etc)
    * `fifo` vs `pinned` queueing strategy

* Any call to any `/setconfig` route for a given host:port will poison ALL cache entries for that host:port
    * Except `/setconfig/dry-run` of course 

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

### public cloud instance
There is a public instance of netpalm available below 
- https://netpalm.tech/
- API key = 2a84465a-cf38-46b2-9d86-b84Q7d57f288

### useful netpalm resources

netpalm getting started blog:
- [netpalm Intro Part 1](https://blog.wimwauters.com/networkprogrammability/2020-04-14_netpalm_introduction_part1/)
- [netpalm Intro Part 2](https://blog.wimwauters.com/networkprogrammability/2020-04-15_netpalm_introduction_part2/)
- [netpalm Intro Part 3](https://blog.wimwauters.com/networkprogrammability/2020-04-17_netpalm_introduction_part3/)

netpalm in the network collective podcast:
- https://networkcollective.com/2020/08/ntc-netpalm/

### netpalm support

we maintain an active community on the networktocode slack channel

#netpalm on networktocode.slack.com


# Contributing
Check out the [Contributing Doc](/CONTRIBUTING.md) in this repo for more info!