#   This code is distributed WITHOUT ANY WARRANTY, without the implied
#   warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#   See the GNU Lesser General Public License for more details.
#   
#   The license is distributed along with this repository or you can check
#   <http://www.gnu.org/licenses/> for more details.
#
# Contributors: 
# marcos-pereira (https://github.com/marcos-pereira)

#!/usr/bin/env python

import numpy as np
import math 
import sys

from coppeliasim_zmqremoteapi_client import *

from YamlDatafile import YamlDatafile

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

def goal_angle(init_config, goal_config):
    """Return the angle between the init config (x, y, phi) and the goal config
    (x_goal, y_goal, phi_goal) about the z-axis.

    Args:
        init_config (_type_): the initial configuration.
        goal_config (_type_): the goal configuration.

    Returns:
        _type_: the angle about the z-axis to the goal configuration.
    """
    delta_x = goal_config[0]-init_config[0]
    delta_y = goal_config[1]-init_config[1]
    goal_angle = np.arctan2(delta_y,delta_x)
    return goal_angle

def get_twist(yaw, xd_vel, yd_vel, d=0.12):
    """Return the robot twist.

    Args:
        yaw (_type_): the robot current yaw angle.
        xd_vel (_type_): the desired x-velocity.
        yd_vel (_type_): the desired y-velocity.
        d (float, optional): the distance from the robot center to a point on the robot. Defaults to 0.12.

    Returns:
        np array: the robot twist.
    """

    # Transform linear and angular velocity (twist) to 
    # x- and y- velocities
    T = np.array([[math.cos(yaw), (-d) * math.sin(yaw)],
                    [math.sin(yaw), d * math.cos(yaw)]])

    # Use the inverse to get the opposite: get twist from linear and angular velocities
    T_inv = np.linalg.inv(T)

    # Control inputs are the x- and y- desired velocities to goal configuration
    u = np.array([[xd_vel],
                    [yd_vel]])

    # Transform from x- and y-velocities to twist
    twist = np.matmul(T_inv, u)

    return (twist)  

def get_wheel_velocities(phi, dot_x, dot_y, wheel_radius=0.195/2.0, l_shaft=0.33):
    """Calculate the robot wheel velocities using nonholonomic constraint jacobian inverse.

    Args:
        phi (float): the robot rotation about the z-axis
        dot_x (float): the desired x-velocity.
        dot_y (float): the desired y-velocity.
        wheel_radius (_type_, optional): the wheel radius. Defaults to 0.195/2.0.
        l_shaft (float, optional): the length of the shaft between wheels. Defaults to 0.33.

    Returns:
        _type_: _description_
    """
    # Get linear and angular velocities (twist) from the desired
    # x- and y- velocities and angle to align with desired configuration
    twist = get_twist(phi, dot_x, dot_y)

    # Transform wheel velocities to twist 
    T_wheel_to_twist = np.array([[1.0/2.0, 1.0/2.0], [1.0/l_shaft, -1.0/l_shaft]])

    # Convert from twist to wheel velocities
    wheel_velocities = np.matmul(np.linalg.inv(T_wheel_to_twist), twist)
    
    # Convert from linear velocity to angular velocity
    angular_wheel_velocities = wheel_velocities/wheel_radius

    return (angular_wheel_velocities)

def euclidean_distance(q1, q2):
    """Return the euclidean distance between configurations q1 (x1, y1, phi1) and q2 (x2, z2, phi2).

    Args:
        q1 (_type_): the first configuration.
        q2 (_type_): the second configuration.

    Returns:
        float: the euclidean distance.
    """
    distance = math.sqrt((q1[0]-q2[0])**2 + (q1[1]-q2[1])**2)
    return distance

def twist_feedback_linearization(x, y, yaw, xd, yd, dot_x, dot_y, gain, d=0.1):
    """Return the twist of the robot using feedback linearization.

    Args:
        x (float): the current x position.
        y (float): the current y position.
        yaw (float): the current yaw of the robot.
        xd (float): the desired x position.
        yd (float): the desired y position.
        dot_x (float): the desired x velocity.
        dot_y (float): the desired y velocity.
        gain (float): the feedback linearization gain.
        d (float, optional): the distance from the robot center to a point on the robot. Defaults to 0.1.

    Returns:
        np array: the robot twist.
    """

    # Transform linear and angular velocity (twist) to 
    # x- and y- velocities
    T = np.array([[math.cos(yaw), (-d) * math.sin(yaw)],
                    [math.sin(yaw), d * math.cos(yaw)]])

    # Use the inverse to get the opposite: get twist from linear and angular velocities
    T_inv = np.linalg.inv(T)

    # Control inputs are the x- and y- desired velocities to goal configuration
    u = np.array([[dot_x + gain*(xd - x)],
                    [dot_y + gain*(yd - y)]])

    # Transform from x- and y-velocities to twist
    twist = np.matmul(T_inv, u)

    return (twist)  

def main():
    
    # Print help 
    if len(sys.argv) < 2:
        print("Usage: python main.py <parameters_file_name.yaml>")
        sys.exit(1)
    
    parameters_file_name = sys.argv[1]    
    parameters_yaml = YamlDatafile.get_all_parameters_from_yaml_file(
            parameters_file_name
        )

    parameters = dict()

    for parameter_name in parameters_yaml:
        value = parameters_yaml[parameter_name]["value"]       
        parameters[parameter_name] = value
        
    # Trajectory type
    trajectory_type = parameters["trajectory_type"]
    
    # Sampling time [seconds]
    sampling_time = parameters["sampling_time"]
    
    # Create trajectory variable
    init_value = parameters["init_value"]
    # Circular trajectory: 360
    # Lemniscate: 360
    last_value = parameters["last_value"]
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

        if trajectory_type == "lemniscate":
            ####################################
            # Lemniscate trajectory
            # # Half lemniscate size
            a = parameters["half_lemniscate_size"]
            # no video: 60
            # video: 180
            lemniscate_period = parameters["lemniscate_period"]
            omega = 2*math.pi/lemniscate_period

            # # x-translation and y-translation
            x = a*np.cos(omega*t_var)/(1+np.sin(omega*t_var)**2)
            y = a*np.sin(omega*t_var)*np.cos(omega*t_var)/(1+np.sin(omega*t_var)**2)
            x_trajectory = np.append(x_trajectory,x)
            y_trajectory = np.append(y_trajectory,y)

            # # x- and y- derivatives
            omega_t = omega*t_var
            x_dot = -(a*omega*np.sin(omega_t)*(np.sin(omega_t)**2 + 2*np.cos(omega_t)**2 + 1))/((np.sin(omega_t)**2 + 1)**2)
            y_dot = -(a*omega*(np.sin(omega_t)**4 + np.sin(omega_t)**2 + (np.sin(omega_t)**2 - 1)*np.cos(omega_t)**2))/((np.sin(omega_t)**2 + 1)**2)
            xdot_trajectory = np.append(xdot_trajectory,x_dot)
            ydot_trajectory = np.append(ydot_trajectory,y_dot)

        elif trajectory_type == "circle":            
            ####################################
            # Circular trajectory
            circle_radius = parameters["circle_radius"]
            # no video: 60.0
            # video: 180.0
            circle_period = parameters["circle_period"]
            omega = 2*np.pi/circle_period
            x = circle_radius*np.cos(omega*t_var)
            y = circle_radius*np.sin(omega*t_var)
            x_trajectory = np.append(x_trajectory,x)
            y_trajectory = np.append(y_trajectory,y)
            x_dot = -omega*circle_radius*np.sin(omega*t_var)
            y_dot = omega*circle_radius*np.cos(omega*t_var)
            xdot_trajectory = np.append(xdot_trajectory,x_dot)
            ydot_trajectory = np.append(ydot_trajectory,y_dot)            

        elif trajectory_type == "epicycloid":        
            ####################################
            # Epicycloid
            a = parameters["epicycloid_a"]
            b = parameters["epicycloid_b"]
            curve_period = parameters["epicycloid_period"]
            omega = 2*math.pi/curve_period

            # # x-translation and y-translation
            x = (a+b)*np.cos(omega*t_var) - b*np.cos((a/b + 1)*omega*t_var)
            y = (a+b)*np.sin(omega*t_var) - b*np.sin((a/b + 1)*omega*t_var)
            x_trajectory = np.append(x_trajectory,x)
            y_trajectory = np.append(y_trajectory,y)

            # # x- and y- derivatives
            omega_t = omega*t_var
            x_dot = omega*(-(a+b))*(np.sin(omega_t)-np.sin((omega_t*(a+b)/b)))
            y_dot = omega*(a+b)*(np.cos(omega_t)-np.cos((omega_t*(a+b))/b))
            xdot_trajectory = np.append(xdot_trajectory,x_dot)
            ydot_trajectory = np.append(ydot_trajectory,y_dot)

        elif trajectory_type == "hypocycloid":
            ####################################
            # Hypocycloid: with the parameters below it will be a tricuspoid
            a = parameters["hypocycloid_a"]
            b = parameters["hypocycloid_b"]
            # no video: 90
            # video: 180
            curve_period = parameters["hypocycloid_period"]
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
    
    desired_alignment_error = parameters["desired_alignment_error"]
    
    robot_handle = sim.getObject("/Pioneer_p3dx_connection4")
    right_motor_handle = sim.getObject("/Pioneer_p3dx_rightMotor")
    left_motor_handle = sim.getObject("/Pioneer_p3dx_leftMotor")
    
    # Align robot with trajectory initial position
    while True:
        robot_position = sim.getObjectPosition(robot_handle, sim.handle_world)
        robot_orientation = sim.getObjectOrientation(robot_handle, sim.handle_world)
        
        (twist_to_align, aligned) = align_with_goal(
            x_trajectory[0], 
            y_trajectory[0], 
            robot_position[0], 
            robot_position[1], 
            robot_orientation[2], 
            desired_alignment_error)
        
        wheel_velocities = twist_to_wheel_velocities(twist_to_align)
    
        sim.setJointTargetVelocity(right_motor_handle, wheel_velocities[0][0])
        sim.setJointTargetVelocity(left_motor_handle, wheel_velocities[1][0])
        
        client.step()
        
        if aligned is True:
            break
        
    desired_euclidean_error = parameters["desired_euclidean_error"]
    
    # Go to trajectory inital position
    while True:
        robot_position = sim.getObjectPosition(robot_handle, sim.handle_world)
        robot_orientation = sim.getObjectOrientation(robot_handle, sim.handle_world)
        
        current_configuration = np.array([robot_position[0], robot_position[1], robot_orientation[2]])
        goal_configuration = np.array([x_trajectory[0], y_trajectory[0], 0])
        
        angle_to_goal = goal_angle(current_configuration, goal_configuration)   
        
        dot_x = math.cos(angle_to_goal)
        dot_y = math.sin(angle_to_goal)
        wheel_velocities = get_wheel_velocities(robot_orientation[2], dot_x, dot_y)  
        
        sim.setJointTargetVelocity(right_motor_handle, wheel_velocities[0][0])
        sim.setJointTargetVelocity(left_motor_handle, wheel_velocities[1][0])     
        
        print("Eucliden distance to goal")
        print(euclidean_distance(current_configuration, goal_configuration))
        
        client.step()

        ## Check if desired euclidean distance was reached
        if euclidean_distance(current_configuration, goal_configuration) < desired_euclidean_error:
            print("Initial position reached.")
            
            sim.setJointTargetVelocity(right_motor_handle, 0.0)
            sim.setJointTargetVelocity(left_motor_handle, 0.0)   
            
            break
        
    control_gain = parameters["control_gain"]
    
    trajectory_reference_handle = sim.getObject("/Sphere")
    
    # Track the trajectory
    for i in range(len(x_trajectory)):
        robot_position = sim.getObjectPosition(robot_handle, sim.handle_world)
        robot_orientation = sim.getObjectOrientation(robot_handle, sim.handle_world)
        
        current_configuration = np.array([robot_position[0], robot_position[1], robot_orientation[2]])
        goal_configuration = np.array([x_trajectory[i], y_trajectory[i], 0])
        
        twist = twist_feedback_linearization(
            current_configuration[0], current_configuration[1], current_configuration[2],
            x_trajectory[i], y_trajectory[i],
            xdot_trajectory[i], ydot_trajectory[i],
            control_gain)
        
        wheel_velocities = twist_to_wheel_velocities(twist)
        
        sim.setJointTargetVelocity(right_motor_handle, wheel_velocities[0][0])
        sim.setJointTargetVelocity(left_motor_handle, wheel_velocities[1][0])    
        sim.setObjectPosition(trajectory_reference_handle, sim.handle_world, (x_trajectory[i], y_trajectory[i], robot_position[2]))
        
        print(f"Trajectory step: {i}, total: {len(x_trajectory)}")
        
        client.step() 
            
    sim.setJointTargetVelocity(right_motor_handle, 0.0)
    sim.setJointTargetVelocity(left_motor_handle, 0.0) 
    
    sim.stopSimulation()
        

if __name__ == '__main__':
    main()