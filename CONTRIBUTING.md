# Guidance on how to contribute

Contributions to this code are welcome and appreciated.
Please adhere to our [Code of Conduct](./CODE_OF_CONDUCT.md) at all times.

> All contributions to this code will be released under the terms of the [LICENSE](./LICENSE) of this code. By submitting a pull request or filing a bug, issue, or feature request, you are agreeing to comply with this waiver of copyright interest. Details can be found in our [LICENSE](./LICENSE).

There are two primary ways to contribute:

1. Using the issue tracker
2. Changing the codebase


## Using the issue tracker

Use the issue tracker to suggest feature requests, report bugs, and ask questions. This is also a great way to connect with the developers of the project as well as others who are interested in this solution.

Use the issue tracker to find ways to contribute. Find a bug or a feature, mention in the issue that you will take on that effort, then follow the _Changing the codebase_ guidance below.


## Changing the codebase

Generally speaking, you should fork this repository, make changes in your own fork, and then submit a pull request. All new code should have associated unit tests (if applicable) that validate implemented features and the presence or lack of defects.

Additionally, the code should follow any stylistic and architectural guidelines prescribed by the project. In the absence of such guidelines, mimic the styles and patterns in the existing codebase.

## Hacking on Netpalm

#### netpalm support

We maintain an active community on the networktocode slack channel.  `#netpalm` on `networktocode.slack.com`.  Come say 'Hi' and Drop a PR! 

## Contributing
### Testing
Testing is vital to the mission of Netpalm.  The goal of this project is to serve as the "glue" that binds many 
different mission critical systems.  If you're going to trust Netpalm to access and even push configuration changes to 
vital infrastructure, you MUST be certain Netpalm is going to behave as-advertised.  Rigorous testing is how we ensure 
the features we implement work as-designed both now, and after inevitable changes later on.

In all cases all we seek to validate is Netpalms behavior itself.  In the unlikely event Netmiko mishandles something
for instance, then we'll rely on the maintainers of that project to identify and address it.

Tests in Netpalm fall into 3 broad categories

* Full integration tests.  These begin with an HTTP request from your local system to a running Netpalm Instance, and 
from there reach out to some router, etc.  Some of these depend on something like a GNS3 lab, others depend on publicly 
reachable devices from Cisco or other vendors.    
  * These are "deep and narrow".  They each test one exact set of conditions fully end-to-end.  They are slow to run and 
    comparatively difficult to write, as such these are the last line of defense.
  * Running this test suite with 30 or so tests selected takes 10 or so minutes.  The intent is to run these as final 
    validation before merges.
  
* "Cisgo" integration tests.  These also begin with an HTTP request to a Netpalm instance, but here netpalm should be 
deployed with access to a `cisgo` instance for much faster test runs.  Right now only a hand full of tests use this model
  * These are still "deep and narrow" but because of the reduced runtime it's feasible to run them far more often. 
  * accessed with `pytest -m cisgo`
  * current runtime on reference machine with 12 tests selected is ~40s
  
* code-only unit tests.  These tests validate core internal Netpalm logic and functionality.  These are meant to be ran 
in-container and require have all the same requirements as the full netpalm execution environment. Everything listed in `requirements.txt` essentially.
  * accessed with `pytest -m nolab`.  Or even `docker-compose -f .\docker-compose.dev.yml run --rm controller pytest -m nolab`
  * current runtime on reference machine with 31 tests selected is ~1.6s
