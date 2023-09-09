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
6. The robot should follow a circle trajectory. Check the main.py to choose another trajectory.

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

# Some references
- Fukao, T., Nakagawa, H., & Adachi, N. (2000). Adaptive tracking control of a nonholonomic mobile robot. IEEE Transactions on Robotics and Automation, 16(5), 609–615. https://doi.org/10.1109/70.880812

- Sarkar, N., Xiaoping Yun, & Kumar, V. (1994). Control of Mechanical Systems With Rolling Constraints. The International Journal of Robotics Research, 13(1), 55–69. https://doi.org/10.1177/027836499401300104

- Kokoska, S. . Fifty Famous Curves, Lots of Calculus Questions, And a Few Answers

- Siciliano, B., Sciavicco, L., Villani, L., & Oriolo, G. (2009). Robotics - Modelling, Planning and Control. 