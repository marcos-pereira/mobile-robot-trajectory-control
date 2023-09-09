#!/usr/bin/env python

import numpy as np
import math 

from coppeliasim_zmqremoteapi_client import *

def main():
    # Sampling time [seconds]
    sampling_time = 0.005
    
    # Create trajectory variable
    init_value = 0.0
    # Circular trajectory: 360
    # Lemniscate: 360
    last_value = 120        
    print("Generating trajectory variable to use in the trajectory parametric equation...")
    trajectory_variable = np.arange(init_value,last_value,sampling_time)       
    x_trajectory = np.array([])
    y_trajectory = np.array([])
    xdot_trajectory = np.array([])
    ydot_trajectory = np.array([])
    
    # Generate trajectory
    for trajectory_step in range(len(trajectory_variable)):            

        # Time (seconds)
        t_var = trajectory_variable[trajectory_step]

        ####################################
        # # Lemniscate trajectory
        # # # Half lemniscate size
        # a = 1.0
        # # no video: 60
        # # video: 180
        # lemniscate_period = 180
        # omega = 2*math.pi/lemniscate_period

        # # # x-translation and y-translation
        # x = a*np.cos(omega*t_var)/(1+np.sin(omega*t_var)**2)
        # y = a*np.sin(omega*t_var)*np.cos(omega*t_var)/(1+np.sin(omega*t_var)**2)
        # x_trajectory = np.append(x_trajectory,x)
        # y_trajectory = np.append(y_trajectory,y)

        # # # x- and y- derivatives
        # omega_t = omega*t_var
        # x_dot = -(a*omega*np.sin(omega_t)*(np.sin(omega_t)**2 + 2*np.cos(omega_t)**2 + 1))/((np.sin(omega_t)**2 + 1)**2)
        # y_dot = -(a*omega*(np.sin(omega_t)**4 + np.sin(omega_t)**2 + (np.sin(omega_t)**2 - 1)*np.cos(omega_t)**2))/((np.sin(omega_t)**2 + 1)**2)
        # xdot_trajectory = np.append(xdot_trajectory,x_dot)
        # ydot_trajectory = np.append(ydot_trajectory,y_dot)

        ####################################
        # # Circular trajectory
        # circle_radius = 1.5 # meters
        # # no video: 60.0
        # # video: 180.0
        # circle_period = 180.0 # seconds
        # omega = 2*pi/circle_period
        # x = circle_radius*np.cos(omega*t_var)
        # y = circle_radius*np.sin(omega*t_var)
        # x_trajectory = np.append(x_trajectory,x)
        # y_trajectory = np.append(y_trajectory,y)
        # x_dot = -omega*circle_radius*np.sin(omega*t_var)
        # y_dot = omega*circle_radius*np.cos(omega*t_var)
        # xdot_trajectory = np.append(xdot_trajectory,x_dot)
        # ydot_trajectory = np.append(ydot_trajectory,y_dot)            

        ####################################
        # # Epicycloid
        # a = 0.5
        # b = 1.0
        # curve_period = 90
        # omega = 2*math.pi/curve_period

        # # # x-translation and y-translation
        # x = (a+b)*np.cos(omega*t_var) - b*np.cos((a/b + 1)*omega*t_var)
        # y = (a+b)*np.sin(omega*t_var) - b*np.sin((a/b + 1)*omega*t_var)
        # x_trajectory = np.append(x_trajectory,x)
        # y_trajectory = np.append(y_trajectory,y)

        # # # x- and y- derivatives
        # omega_t = omega*t_var
        # x_dot = omega*(-(a+b))*(np.sin(omega_t)-np.sin((omega_t*(a+b)/b)))
        # y_dot = omega*(a+b)*(np.cos(omega_t)-np.cos((omega_t*(a+b))/b))
        # xdot_trajectory = np.append(xdot_trajectory,x_dot)
        # ydot_trajectory = np.append(ydot_trajectory,y_dot)

        ####################################
        # Hypocycloid: with the parameters below it will be a tricuspoid
        a = 1.5
        b = 0.5
        # no video: 90
        # video: 180
        curve_period = 180
        omega = 2*math.pi/curve_period

        # # x-translation and y-translation
        x = (a-b)*np.cos(omega*t_var) + b*np.cos((a/b - 1)*omega*t_var)
        y = (a-b)*np.sin(omega*t_var) - b*np.sin((a/b - 1)*omega*t_var)
        x_trajectory = np.append(x_trajectory,x)
        y_trajectory = np.append(y_trajectory,y)

        # # x- and y- derivatives
        omega_t = omega*t_var
        x_dot = omega*(-(a-b))*(np.sin(omega_t)+np.sin(omega_t*(a/b -1)))
        y_dot = omega*(a-b)*(np.cos(omega_t)-np.cos(omega_t*(a/b -1)))
        xdot_trajectory = np.append(xdot_trajectory,x_dot)
        ydot_trajectory = np.append(ydot_trajectory,y_dot)
        
    # create a client to connect to zmqRemoteApi server:
    # (creation arguments can specify different host/port,
    # defaults are host='localhost', port=23000)
    client = RemoteAPIClient()
    
    # get a remote object:
    sim = client.getObject('sim')
    
    client.setStepping(True)
    
    sim.startSimulation()

if __name__ == '__main__':
    main()