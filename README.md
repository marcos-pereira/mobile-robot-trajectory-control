# mobile-robot-trajectory-control
Trajectory control for a mobile robot in CoppeliaSim.

# How to run the code
1. Download [CoppeliaSim](https://www.coppeliarobotics.com/).
2. If you are on Linux, go the folder where you extracted then run it:
```
cd folder/where/coppeliasim/is
./coppeliaSim.sh
``` 
3. From CoppeliaSim, open the simulation scene pioneer_p3dx.ttt that is located in this repository.
4. Install the Zmq Interface for CoppeliaSim in Python (see instructions below).
5. Run the main.py script:
```
cd python-scripts
python3 main.py
```

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