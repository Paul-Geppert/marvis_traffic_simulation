# Marvis traffic simulation

In this repo a simple traffic simulation is implemented: A train crosses a street at an unguarded level crossing. The train is sensed by its CAM messages.

Marvis and ns-3 are included as submodules, so please `git clone --recurse-submodules https://github.com/Paul-Geppert/marvis_traffic_simulation` to clone this repo.

* Marvis has the MobilityProvider implemented and its functions are exposed via an XML-RPC server
* ns-3 basically is the same as [https://github.com/FabianEckermann/ns-3_c-v2x](https://github.com/FabianEckermann/ns-3_c-v2x), but bindings for Python 3.8 will be generated too.

## Requirements

Depending on how you want to execute and develop the converter simulation you will need:

* Docker ([https://www.docker.com/](https://www.docker.com/))
* SUMO ([https://www.eclipse.org/sumo/](https://www.eclipse.org/sumo/))
* Python 3.8: ns-3_c-v2x will be compiled for Python 3.8, make sure your environment is compatible.
* Python packages:
  * coloredlogs
  * nsenter
  * paramiko
  * pylxd
  * pyroute2
  * git+https://github.com/active-expressions/active-expressions-static-python
  
  * docker
  * pyyaml
  * six
  * pyutil
  * pytz

## Build and execute on host machine

0. Clone the repository and it's submodules.
1. Compile the ns-3_c-v2x simulator. This will take some time. A Docker container that contains all relevant requirements will be created and the build starts automatically. Also note that the first compilation will fail as the Bindings cannot be completely generated. A fix will be applied by the script and it will continue to compile ns-3, which should be successful now.

```sh
cd ns-3_c-v2x
./compile.sh
cd ..
```

If the build container is not close automatically, leave it by calling `exit`.

2. Adapt the `SUMO_HOME` and `PYTHON_TO_USE` variable in `./start-tdis-simulation.sh` with yout local SUMO path and python.
3. Use the start script: `sudo ./start-tdis-simulation.sh`. Please note that the execution needs higher privileges.

## Troubleshooting

Containers might have problems to access services bound on `docker0` interface. If this is the case, you might want to check your firewall and routing rules. This command might fix the problem: `iptables -A INPUT -i docker0 -j ACCEPT`. Find more information here: [https://stackoverflow.com/questions/31324981/how-to-access-host-port-from-docker-container](https://stackoverflow.com/questions/31324981/how-to-access-host-port-from-docker-container)
