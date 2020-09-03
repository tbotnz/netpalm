#Running the Netpalm Test Suite

## Caveat:
Like most things, there are many many ways to do this.  This is simply documenting one known-working method.  Tools like
docker-compose and pytest have their own excellent documentation, so be sure to refer there for more details on how to 
tweak this process.

### 3 categories of tests
1. Full Integration Tests - not covered here because I don't know how to run them :(
2. "Cisgo" integration tests - like full integration tests, but tested against a "cisgo" container, 
rather than real hardware
3. Code-only unit tests - validate core internal Netpalm logic.  Requires Redis, but no other outside interaction at all

### Environment
This doc assumes the following environment:
* Windows 10 Pro with Windows Subsystem for Linux 2 (Ubuntu 20.04)

The hope is that this process is replicable more or less as-is on any modern platform.

#### Environment Setup
starting from scratch, clone the netpalm repo and checkout the branch or commit you'd like to test:
```bash
user@LAPTOP-6PM8GPB2:/mnt/c/projects/empty$ ls -alh
total 0
drwxrwxrwx 1 user user 4.0K Sep  2 16:09 .
drwxrwxrwx 1 user user 4.0K Sep  2 16:09 ..
user@LAPTOP-6PM8GPB2:/mnt/c/projects/empty$ git clone https://github.com/tbotnz/netpalm.git
Cloning into 'netpalm'...
    <truncated>
user@LAPTOP-6PM8GPB2:/mnt/c/projects/empty$ cd netpalm/
user@LAPTOP-6PM8GPB2:/mnt/c/projects/empty/netpalm$ ls
CODE_OF_CONDUCT.md  README.md               dockerfiles                      pytest.ini              worker.py
CONTRIBUTING.md     config                  gunicorn.conf.py                 redis_gen_new_certs.sh
LICENSE             docker-compose.dev.yml  netpalm                          static
NOTICE              docker-compose.yml      netpalm.postman_collection.json  tests
```

We want to test the `cisgo_dockerfile` branch.
```bash
user@LAPTOP-6PM8GPB2:/mnt/c/projects/empty/netpalm$ git checkout -b cisgo_dockerfile origin/cisgo_dockerfile
```

```bash
user@LAPTOP-6PM8GPB2:/mnt/c/projects/empty/netpalm$ docker-compose -f ./docker-compose.dev.yml up --build --force-recreate -V
Building redis
Step 1/5 : FROM redis
 ---> 1319b1eaa0b7
...
Successfully tagged netpalm_redis:latest
Building cisgo
Step 1/6 : FROM golang:1.15.0-buster
 ---> 75605a415539
...
Successfully tagged netpalm_cisgo:latest
Building controller
Step 1/12 : FROM python:3.8
 ---> 6feb119dd186
...
Successfully tagged netpalm_controller:latest
Recreating netpalm_cisgo_1 ... done
Recreating netpalm_redis_1 ... done
Recreating netpalm_worker-fifo_1   ... done
Recreating netpalm_second-ctrlr_1  ... done
Recreating netpalm_controller_1    ... done
Recreating netpalm_worker-pinned_1 ... done
...
cisgo_1          | 2020/09/02 20:29:21 starting cis.go ssh server on port :10000
cisgo_1          | 2020/09/02 20:29:21 starting cis.go ssh server on port :10028
cisgo_1          | 2020/09/02 20:29:21 starting cis.go ssh server on port :10016
...
redis_1          |            _.-``__ ''-._
redis_1          |       _.-``    `.  `_.  ''-._           Redis 6.0.6 (00000000/0) 64 bit
redis_1          |   .-`` .-```.  ```\/    _.,_ ''-._
redis_1          |  (    '      ,       .-`  | `,    )     Running in standalone mode
redis_1          |  |`-._`-...-` __...-.``-._|'` _.-'|     Port: 6379
...
second-ctrlr_1   | [2020-09-02 20:29:28 +0000] [8] [INFO] Booting worker with pid: 8
second-ctrlr_1   | [2020-09-02 20:29:28 +0000] [9] [INFO] Booting worker with pid: 9
controller_1     | [2020-09-02 20:29:28 +0000] [1] [INFO] Starting gunicorn 20.0.4
controller_1     | [2020-09-02 20:29:28 +0000] [1] [INFO] Listening at: http://0.0.0.0:9000 (1)
controller_1     | [2020-09-02 20:29:28 +0000] [1] [INFO] Using worker: uvicorn.workers.Uvi
...
```

This terminal is now occupied w/ docker-compose and will stay that way while we test.  can always add `-d` to the 
docker-compose command to force this to background, but it's handy to see this output anyway.  



## Running Cisgo tests

We'll actually run our tests from another terminal now.

We're actually going to execute these from inside the controller container. 
```bash
user@LAPTOP-6PM8GPB2:/mnt/c/projects/empty/netpalm$ docker-compose -f docker-compose.dev.yml exec controller bash
root@33c8c7cdd563:/code# pytest -m cisgo
================================================= test session starts ==================================================
platform linux -- Python 3.8.5, pytest-6.0.1, py-1.9.0, pluggy-0.13.1
rootdir: /code, configfile: pytest.ini, testpaths: tests
plugins: timeout-1.4.2
collected 80 items / 68 deselected / 12 selected

tests/test_getconfig_cisgo.py ....F....                                                                          [ 75%]
tests/test_setconfig_cisgo.py ...                                                                                [100%]

 <truncated> 

=============================================== short test summary info ================================================
FAILED tests/test_getconfig_cisgo.py::test_getconfig_napalm_getter - TypeError: 'NoneType' object is not subscriptable
=============================== 1 failed, 11 passed, 68 deselected, 2 warnings in 39.30s ===============================
root@33c8c7cdd563:/code#
```

So we've got one failing test.

## Running nolab tests
Same as above, we'll be running this from inside the controller container:
```bash
root@33c8c7cdd563:/code# pytest -m nolab
================================================= test session starts ==================================================
platform linux -- Python 3.8.5, pytest-6.0.1, py-1.9.0, pluggy-0.13.1
rootdir: /code, configfile: pytest.ini, testpaths: tests
plugins: timeout-1.4.2
collected 80 items / 49 deselected / 31 selected

tests/test_confload.py ...                                                                                       [  9%]
tests/test_router_utils.py ....................                                                                  [ 74%]
tests/test_tfsm_templates.py ....                                                                                [ 87%]
tests/test_update_log.py ....                                                                                    [100%]

==================================== 31 passed, 49 deselected, 2 warnings in 2.02s =====================================
root@33c8c7cdd563:/code#
```

