<p align="center">
<img src="/static/images/np_new.png" />
</p>


## what the netpalm

netpalm is a REST API platform for network devices, netpalm makes it easy to push and pull state from your apps to your network.

Leveraging best of breed open source network components like [napalm](https://github.com/napalm-automation/napalm), [netmiko](https://github.com/ktbyers/netmiko),  [ncclient](https://github.com/ncclient/ncclient) and [requests](https://github.com/psf/requests), netpalm makes it easy to abstract from any network devices native telnet, SSH, NETCONF or RESTCONF interface into a modern model driven open api 3 interface.

Taking a platform based approach means netpalm allows you to bring your own jinja2 config, service and webhook templates, python scripts and webhooks for quick adoption into your existing devops workflows.

Built on a scalable microservice based architecture netpalm provides unparalleled scalable API access into your network.

## core platform features

- Speaks REST and JSON RPC northbound, then CLI over SSH or Telnet or NETCONF/RESTCONF southbound to your network devices
- Turns any Python script into a easy to consume, asynchronous and documented API with webhook support
- Large amount of supported network device vendors thanks to [napalm](https://github.com/napalm-automation/napalm), [netmiko](https://github.com/ktbyers/netmiko),  [ncclient](https://github.com/ncclient/ncclient) and [requests](https://github.com/psf/requests)
- Built in multi-level abstraction interface for network service lifecycle functions for Create, Retrieve and Delete
- Ability to write your own [service models and templates](https://github.com/tbotnz/netpalm/tree/master/netpalm/backend/plugins/extensibles/j2_service_templates) using your own existing [jinja2 templates](https://github.com/tbotnz/netpalm/tree/master/netpalm/backend/plugins/extensibles/custom_scripts)
- Well documented API with [postman collection](https://documenter.getpostman.com/view/2391814/T1DqgwcU?version=latest#33acdbb8-b5cd-4b55-bc67-b15c328d6c20) full of examples and every instance gets it own openAPI 3 and self documenting for your service templates and scripts
- Supports pre and post checks accross CLI devices raising exceptions and not deploying config as required
- Multiple ways to queue jobs to devices, either pinned strict task by task to each device or pooled first in first out
- Modern, container based scale out architecture supported by every component
- Highly [configurable](https://github.com/tbotnz/netpalm/blob/master/config/config.json) for all aspects of the platform
- Leverages an ecrypted Redis layer providing caching and queueing of jobs to and from devices

## concepts

netpalm acts as a ReST broker and abstraction layer for NAPALM, Netmiko, NCCLIENT or a Python Script.
netpalm uses TextFSM or Jinja2 to model and transform both ingress and egress data if required.
You make an API call to netpalm and it will establish a queue to your device and start sending configuration

![netpalm concept](/static/images/arch.png)

### additional platform features

- Jinja2
   - BYO jinja2 [config templates](https://github.com/tbotnz/netpalm/tree/master/netpalm/backend/plugins/extensibles/j2_config_templates)
   - BYO jinja2 [service templates](https://github.com/tbotnz/netpalm/tree/master/netpalm/backend/plugins/extensibles/j2_service_templates)
   - BYO jinja2 [webhook templates](https://github.com/tbotnz/netpalm/tree/master/netpalm/backend/plugins/extensibles/j2_webhook_templates)
   - Can be used to just redner Jinja2 templates via the REST API
   - Automatically generates a JSON schema for any Jinja2 Template
   
- Parsers
   - TextFSM support via netmiko
   - [NTC-templates](https://github.com/networktocode/ntc-templates) for parsing/structuring device data (includes)
   - Napalm getters
   - Genie support via netmiko
   - Automated download and installation of TextFSM templates from http://textfsm.nornir.tech online TextFSM development tool
   - Optional dynamic rendering of Netconf XML data into JSON

- Webhooks
   - Comes with standard REST webhook which supports data transformation via your own [jinja2 template](https://github.com/tbotnz/netpalm/tree/master/netpalm/backend/plugins/extensibles/j2_webhook_templates)
   - Supports you to bring your own (BYO) [webhook scripts](https://github.com/tbotnz/netpalm/tree/master/netpalm/backend/plugins/extensibles/custom_webhooks)

- Scripts
   - Execute ANY python [script](https://github.com/tbotnz/netpalm/tree/master/netpalm/backend/plugins/extensibles/custom_scripts/hello_world.py) as async via the ReST API and includes passing in of parameters
   - Supports pydantic [models](https://github.com/tbotnz/netpalm/blob/master/netpalm/backend/plugins/extensibles/custom_scripts/hello_world_model.py) for data validation and documentation

- Queueing 
   - Supports a "pinned" queueing strategy where a dedicated process and queue is established for your device, tasks are sync queued and processed for that device
   - Supports a "fifo" pooled queueing strategy where a pool of workers 
   - Supports on the fly changes to the async queue strategy for a device

- Caching
   - Can cache responses from devices so that the same request doesnt have to go back to the device
   - Automated cache poisioning on config changes on devices

- Scaling
   - Horizontal container based scale out architecture supported by each component

## basic netpalm example

We can show you examples for days we reccomend checking the online [postman collection](https://documenter.getpostman.com/view/2391814/T1DqgwcU?version=latest#33acdbb8-b5cd-4b55-bc67-b15c328d6c20) to get a feel for what can be done.
We also host a [public instance](https://netpalm.tech) have a look at the swagger ui

### getconfig method

netpalm also supports all arguments for the transport libs, simply pass them in as below

![netpalm eg3](/static/images/netpalm_eg_3.png)

#### check response

![netpalm eg4](/static/images/netpalm_eg_4.png)

### service templates in action

netpalm supports model driven service templates, these self render an OpenAPI 3 interface and provide abstraction and orchestration of tasks accross many devices using the get/setconfig or script methods.

The below example demonstrates basic SNMP state orchestration accross multiple devices for create, retrieve, delete 

![netpalm auto ingest](/static/images/np_service.gif)

### rapid template development and deployment

netpalm is integrated into http://textfsm.nornir.tech so you can ingest your templates with ease

![netpalm auto ingest](/static/images/netpalm_ingest.gif)

### API documentation

netpalm comes with a [postman collection](https://documenter.getpostman.com/view/2391814/T1DqgwcU?version=latest#33acdbb8-b5cd-4b55-bc67-b15c328d6c20) and an OpenAPI based API with swagger ui
![netpalm swagger](/static/images/oapi.png)

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

