![netpalm_log](/static/images/netpalm.png)
# Hacking on Netpalm

### netpalm support

We maintain an active community on the networktocode slack channel.  `#netpalm` on `networktocode.slack.com`.  Come say 'Hi' and Drop a PR! 

# Contributing
## Testing
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
  
* Cisgo integration tests.  These also begin with an HTTP request to a Netpalm instance, but here netpalm should be 
deployed with access to a `cisgo` instance for much faster test runs.  Right now only a hand full of tests use this model
  * These are still "deep and narrow" but because of the reduced runtime it's feasible to run the far more often. 
  * accessed with `pytest -m cisgo`
  * current runtime on reference machine with 3 tests selected is ~3.5s
  
* code-only unit tests.  These tests validate core internal Netpalm logic and functionality.  These are meant to be ran 
in-container and require have all the same requirements as the full netpalm execution environment. Everything listed in `requirements.txt` essentially.
  * accessed with `pytest -m nolab`
  * current runtime on reference machine with 31 tests selected is ~1.6s

