
<p align="center">
   <br/>
   <img src="/static/images/np_new.png" />
   <br/>
   <h3 align="center">The Open API Platform for Network Devices</h3>
   <br/>
   <p align="center">
   netpalm makes it easy to push and pull state from your apps to your network by providing multiple southbound drivers, abstraction methods and modern northbound  interfaces such as open API3 and REST webhooks.
   </p>
   <p align="center" style="align: center;">
      <img src="https://github.com/tbotnz/netpalm/workflows/tests/badge.svg" alt="Tests"/>
      <a href="https://networktocode.slack.com" alt="NTC Slack"><img src="https://img.shields.io/badge/slack-networktocode-orange" alt="NTC Slack" /></a>
      <img src="https://img.shields.io/github/issues/tbotnz/netpalm" alt="Github Issues" />
      <img src="https://img.shields.io/github/issues-pr/tbotnz/netpalm" alt="Github Pull Requests" />
      <img src="https://img.shields.io/github/stars/tbotnz/netpalm" alt="Github Stars" />
      <img src="https://img.shields.io/github/contributors-anon/tbotnz/netpalm" alt="Github Contributors" />
      <img src="https://img.shields.io/github/v/release/tbotnz/netpalm?include_prereleases" alt="Github Release" />
      <img src="https://img.shields.io/github/license/tbotnz/netpalm" alt="License" />
   </p>
</p>

<h2 align="center">Supporting netpalm</h2>


<!--sponsors start-->
<table>
  <tbody>
    <tr>
      <td align="center" valign="middle">
        <a href="https://www.apcela.com" target="_blank">
          <img width="222px" src="https://www.apcela.com/wp-content/uploads/2020/11/apcela-white-black.png" alt="Apcela" />
        </a><br />
        <div>Apcela</div><br />
        <i><sub>Because Enterprise Speed Matters</sub></i>
      </td>
       <td align="center" valign="middle">
        <a href="https://www.bandwidth.com" target="_blank">
          <img width="222px" src="https://www.bandwidth.com/wp-content/uploads/BW_tm_RGB_horO_Blue.png" alt="Bandwidth" />
        </a><br /><br /><br />
        <i><sub>Delivering the power to communicate</sub></i>
      </td>
      <td align="center" valign="middle">
        <a href="mailto:tonynealon1989@gmail.com" target="_blank">
          <img width="120px" src="https://imgur.com/X1gKuY0.png" alt="Support" />
        <br />
        <div>Maybe you?</div></a>
      </td>
      <!-- <td align="center" valign="middle">
        <a href="#" target="_blank"></a>
      </td> -->
    </tr><tr></tr>
  </tbody>
</table>
<!--sponsors end-->

## Table of Contents

* [What is netpalm?](#what-is-netpalm)
* [Features](#features)
* [Configuration](#configuration)
* [Installation](#installation)
* [Scaling](#scaling)
* [Concepts](#concepts)
* [Additional Features](#additional-features)
* [Examples](#examples)
* [API Docs](#api-docs)
* [Caching](#caching)
* [Further Reading](#further-reading)
* [Contributing](#contributing)


## What is netpalm?

netpalm makes it easy to integrate your network into your automation architecture.

<p align="center">
<img src="/static/images/np-basic-new.png">
</p>

Leveraging best of breed open source network components like [napalm](https://github.com/napalm-automation/napalm), [netmiko](https://github.com/ktbyers/netmiko),  [ncclient](https://github.com/ncclient/ncclient) and [requests](https://github.com/psf/requests), netpalm makes it easy to abstract from any network devices native telnet, SSH, NETCONF or RESTCONF interface into a modern model driven open api 3 interface.

Taking a platform based approach means netpalm allows you to bring your own jinja2 config, service and webhook templates, python scripts and webhooks for quick adoption into your existing devops workflows.

Built on a scalable microservice based architecture netpalm provides unparalleled scalable API access into your network.

## Features

- Speaks REST and JSON RPC northbound, then CLI over SSH or Telnet or NETCONF/RESTCONF southbound to your network devices
- Turns any Python script into a easy to consume, asynchronous and documented API with webhook support
- Large amount of supported network device vendors thanks to [napalm](https://github.com/napalm-automation/napalm), [netmiko](https://github.com/ktbyers/netmiko),  [ncclient](https://github.com/ncclient/ncclient) and [requests](https://github.com/psf/requests)
- Built in multi-level abstraction interface for network service lifecycle functions for create, retrieve and delete and validate
- In band service inventory
- Ability to write your own [service models and templates](https://github.com/tbotnz/netpalm/tree/master/netpalm/backend/plugins/extensibles/j2_service_templates) using your own existing [jinja2 templates](https://github.com/tbotnz/netpalm/tree/master/netpalm/backend/plugins/extensibles/custom_scripts)
- Well documented API with [postman collection](https://documenter.getpostman.com/view/2391814/T1DqgwcU?version=latest#33acdbb8-b5cd-4b55-bc67-b15c328d6c20) full of examples and every instance gets it own self documenting openAPI 3 UI.
- Supports pre and post checks accross CLI devices raising exceptions and not deploying config as required
- Multiple ways to queue jobs to devices, either pinned strict (prevent connection pooling at device)or pooled first in first out
- Modern, container based scale out architecture supported by every component
- Highly [configurable](https://github.com/tbotnz/netpalm/blob/master/config/config.json) for all aspects of the platform
- Leverages an ecrypted Redis layer providing caching and queueing of jobs to and from devices


## Concepts

### Functional Concepts
netpalm acts as a ReST broker and abstraction layer for NAPALM, Netmiko, NCCLIENT or a Python Script.
netpalm uses TextFSM or Jinja2 to model and transform both ingress and egress data if required.
You make an API call to netpalm and it will establish a queue to your device and start sending configuration

<p align="center">
<img src="/static/images/np-basic-new2.png">
</p>

### Component Concepts
netpalm is underpinned by a container based scale out architecture.

<p align="center">
<img src="/static/images/np-basic-q.png">
</p>

### Queueing Concepts
netpalm provides domain focused queueing strategy for task execution.

<p align="center">
<img src="/static/images/np-component.png">
</p>


## Scaling

netpalm containers can be scaled in and out as required. You can define how many containers are required of each type in the `docker-compose` command

```
docker-compose scale netpalm-controller=1 netpalm-worker-pinned=2 netpalm-worker-fifo=3
```


## Additional Features

- Jinja2
   - BYO jinja2 [config templates](https://github.com/tbotnz/netpalm/tree/master/netpalm/backend/plugins/extensibles/j2_config_templates)
   - BYO jinja2 [service templates](https://github.com/tbotnz/netpalm/tree/master/netpalm/backend/plugins/extensibles/j2_service_templates)
   - BYO jinja2 [webhook templates](https://github.com/tbotnz/netpalm/tree/master/netpalm/backend/plugins/extensibles/j2_webhook_templates)
   - Can be used to just redner Jinja2 templates via the REST API
   - Automatically generates a JSON schema for any Jinja2 Template
   
- Parsers
   - TextFSM support via netmiko
   - [NTC-templates](https://github.com/networktocode/ntc-templates) for parsing/structuring device data (includes)
   - [TTP](https://ttp.readthedocs.io/en/latest/) Template Text Parser - Jinja2-like parsing of semi-structured CLI data
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

## Examples

We could show you examples for days, but we recommend playing with the online [postman collection](https://documenter.getpostman.com/view/2391814/T1DqgwcU?version=latest#33acdbb8-b5cd-4b55-bc67-b15c328d6c20) to get a feel for what can be done. We also host a [public instance](https://netpalm.tech) where you can test netpalm via the Swagger UI.

<details>
   <summary style="display:inline-block;" markdown="span"><strong><code>getconfig</code> method</strong></summary>
  
netpalm also supports all arguments for the transport libs, simply pass them in as below

![netpalm eg3](/static/images/netpalm_eg_3.png)
</details>

<details>
   <summary style="display:inline-block;" markdown="block"><strong style="display:inline-block;">check response</strong></summary>
  
![netpalm eg4](/static/images/netpalm_eg_4.png)
</details>

<details>
   <summary style="display:inline-block;"><strong style="display:inline-block;">ServiceTemplates</strong></summary>
  
netpalm supports model driven service templates, these self render an OpenAPI 3 interface and provide abstraction and orchestration of tasks accross many devices using the get/setconfig or script methods.

The below example demonstrates basic SNMP state orchestration accross multiple devices for create, retrieve, delete 

![netpalm auto ingest](/static/images/np_service.gif)
</details>

<details>
   <summary><strong style="display:inline-block;">Template Development and Deployment</strong></summary>
  
netpalm is integrated into http://textfsm.nornir.tech so you can ingest your templates with ease

![netpalm auto ingest](/static/images/netpalm_ingest.gif)
</details>


## API Docs

netpalm comes with a [Postman Collection](https://documenter.getpostman.com/view/2391814/T1DqgwcU?version=latest#33acdbb8-b5cd-4b55-bc67-b15c328d6c20) and an OpenAPI based API with a SwaggerUI located at [`http://localhost:9000/`](http://localhost:9000) after starting the container.

![netpalm swagger](/static/images/oapi.png)

## Caching

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

## Configuration

Edit the `config/config.json` file to change any parameters

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

## Installation

1. Ensure you first have docker installed
```
sudo apt-get install docker.io
sudo apt-get install docker-compose
```

2. Clone this repository
```
git clone https://github.com/tbotnz/netpalm.git
cd netpalm
```

3. Build the container
```
sudo docker-compose up -d --build
```

4. After the container has been built and started, you're good to go! netpalm will be available on port `9000` under your docker hosts IP.
```
http://$(yourdockerhost):9000
```


## Further Reading

- [Cisco Developer Portal](https://developer.cisco.com/codeexchange/github/repo/tbotnz/netpalm/)

- [Wim Wauters - netpalm Intro Part 1](https://blog.wimwauters.com/networkprogrammability/2020-04-14_netpalm_introduction_part1/)
- [Wim Wauters - netpalm Intro Part 2](https://blog.wimwauters.com/networkprogrammability/2020-04-15_netpalm_introduction_part2/)
- [Wim Wauters - netpalm Intro Part 3](https://blog.wimwauters.com/networkprogrammability/2020-04-17_netpalm_introduction_part3/)

- [NetworkCollective w/ Jason Edelman - Podcast Episode about NTC / netpalm](https://networkcollective.com/2020/08/ntc-netpalm/)
- [Packetflow - Top 5 Up and Coming Network Automation Tools](https://www.packetflow.co.uk/top-5-up-and-coming-network-automation-tools/)

- [ipspace - _Building Multivendor Network Automation Platform_](https://blog.ipspace.net/2020/06/reinventing-napalm.html)
- [ipspace - _Useful Network Automation Tools_](https://www.ipspace.net/kb/Ansible/Useful_Network_Automation_Tools.html)

## Contributing

We are open to contributions, before making a PR, please make sure you've read our [`CONTRIBUTING.md`](https://github.com/tbotnz/netpalm/blob/master/CONTRIBUTING.md) document.

You can also find us in the channel `#netpalm` on the [networktocode Slack](https://networktocode.slack.com).

