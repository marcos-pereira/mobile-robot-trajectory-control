#!/usr/bin/env python

import numpy as np
import math 

from coppeliasim_zmqremoteapi_client import *

def align_with_goal(xd, yd, xm, ym, theta_m, desired_error):
    """Return the twist to apply to robot such that it aligns with the 
    desired position (xd, yd) given the measured position (xm, ym), and
    the measured orientation about the z-axis (theta_m).

    Args:
        xd (float): the desired x position.
        yd (float): the desired y position.
        xm (float): the measured x position.
        ym (float): the measured y position.
        theta_m (float): the measured orientation about the z-axis.
        desired_error (float): the desired alignment error to reach.
    """
    # Get current alignment angle
    delta_x = xd - xm
    delta_y = yd - ym
    theta_ref = np.arctan2(delta_y,delta_x)

    # The linear velocity is zero, since we are aligning
    V = 0

    # The angular velocity is the difference to align
    Wz = theta_ref - theta_m

    # Store twist
    twist = np.array([[V],[Wz]])
        
    # If not aligned, return 0
    aligned = False
    if abs(theta_ref - theta_m) < desired_error:
        # If within error tolerance to align
        aligned = True

    return(twist, aligned)

def twist_to_wheel_velocities(twist, wheel_radius=0.195/2.0, l_shaft=0.33):
    """Return the wheel velocities for a given twist.

    Args:
        twist (_type_): the desired twist
        wheel_radius (float, optional): the wheel radius. Defaults to 0.195/2.0.
        l_shaft (float, optional): the length of the shaft between wheels. Defaults to 0.33.

    Returns:
        np array: the right and left wheel velocities.
    """
    # Transform wheel velocities to twist 
    T_wheel_to_twist = np.array([[1.0/2.0, 1.0/2.0], [1.0/l_shaft, -1.0/l_shaft]])

    # Convert from twist to wheel velocities
    wheel_velocities = np.matmul(np.linalg.inv(T_wheel_to_twist), twist)
    
    # Convert from linear velocity to angular velocity
    angular_wheel_velocities = wheel_velocities/wheel_radius

    return (angular_wheel_velocities)

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
        
    client = RemoteAPIClient()
    sim = client.getObject('sim')    
    client.setStepping(True)
    
    sim.startSimulation()
    
    desired_alignment_error = 0.01
    
    robot_handle = sim.getObject("/Pioneer_p3dx_connection4")
    right_motor_handle = sim.getObject("/Pioneer_p3dx_rightMotor")
    left_motor_handle = sim.getObject("/Pioneer_p3dx_leftMotor")
    
    while True:
        robot_pose = sim.getObjectPosition(robot_handle, sim.handle_world)
        robot_orientation = sim.getObjectOrientation(robot_handle, sim.handle_world)
        
        (twist_to_align, aligned) = align_with_goal(
            x_trajectory[0], 
            y_trajectory[0], 
            robot_pose[0], 
            robot_pose[1], 
            robot_orientation[2], 
            desired_alignment_error)
        
        wheel_velocities = twist_to_wheel_velocities(twist_to_align)
    
        sim.setJointTargetVelocity(right_motor_handle, wheel_velocities[0][0])
        sim.setJointTargetVelocity(left_motor_handle, wheel_velocities[1][0])
        
        client.step()
        
        if aligned is True:
            break
        
    sim.stopSimulation()
        

if __name__ == '__main__':
    main()