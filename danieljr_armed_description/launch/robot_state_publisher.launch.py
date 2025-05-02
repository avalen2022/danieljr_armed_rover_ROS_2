from os.path import join
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch import conditions
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import launch_ros.descriptions

def generate_launch_description():
    # Declare arguments
    description_file = LaunchConfiguration("description_file", default="danieljr_armed.urdf.xacro")
    prefix = LaunchConfiguration("prefix", default="")
    use_sim_time = LaunchConfiguration('use_sim_time' , default='true')
    use_gui = LaunchConfiguration('use_gui', default='false')

    declare_use_gui = DeclareLaunchArgument('use_gui', default_value='false', description='Whether to use the GUI for joint state publisher')

    robot_description_content = Command([
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([FindPackageShare("danieljr_armed_description"), "robots", description_file]),
    ])

    robot_description_param = launch_ros.descriptions.ParameterValue(robot_description_content, value_type=str)

    rviz_config_file = PathJoinSubstitution([
        FindPackageShare("danieljr_armed_description"),
        "rviz",
        "robot.rviz"
    ])

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        #namespace=robot_id,
        output='screen',
        parameters=[{
          'use_sim_time': use_sim_time,
          'robot_description': robot_description_param,
          'publish_frequency': 100.0,
          'frame_prefix': prefix,
        }],
    )

    joint_state_publisher_node = Node(
        condition=conditions.UnlessCondition(LaunchConfiguration("use_gui")),
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher_gui',
        output='screen',
    )

    joint_state_publisher_gui_node = Node(
        condition=conditions.IfCondition(LaunchConfiguration("use_gui")),
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher',
        output='screen',
    )

    nodes = [
        declare_use_gui,
        robot_state_publisher_node,
        joint_state_publisher_node,
        joint_state_publisher_gui_node,
        rviz_node,
    ]

    return LaunchDescription(nodes)