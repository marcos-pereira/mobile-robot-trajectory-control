# mobile-robot-trajectory-control
Trajectory control for a mobile robot in CoppeliaSim.

# Installing Zmq Interface for CoppeliaSim and Python
Follow the instructions on [this link](https://github.com/CoppeliaRobotics/zmqRemoteApi/tree/master/clients/python).
```
python3 -m pip install coppeliasim-zmqremoteapi-client
```
Simple example of using the zmq interface to start the simulation:
```
client = RemoteAPIClient()
    
sim = client.getObject('sim')

client.setStepping(True)

sim.startSimulation()
```