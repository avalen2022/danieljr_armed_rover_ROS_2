from os.path import join
from os import environ, pathsep
from ament_index_python.packages import get_package_share_directory, get_package_prefix
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable, IncludeLaunchDescription, OpaqueFunction
from launch.substitutions import PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder

# Function to start the Gazebo server and client
def start_gzserver(context, *args, **kwargs):  
    # TBD: Define pkg_path
    pkg_path = get_package_share_directory('urjc_excavation_world')
    # world_name = 'small_house'
    world_name = LaunchConfiguration('world_name').perform(context)
    # TBD: Define world path

    # Launch Gazebo server
    start_gazebo_server_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(get_package_share_directory('ros_gz_sim'), 'launch',
                         'gz_sim.launch.py')),
        launch_arguments={'gz_args': ['-r -s -v 4 ', world_name]}.items()
    )

    # Launch Gazebo client
    start_gazebo_client_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(get_package_share_directory('ros_gz_sim'),
                         'launch',
                         'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': [' -g ']}.items(),
    )

    return [start_gazebo_server_cmd, start_gazebo_client_cmd]

# Function to get the model paths
def get_model_paths(packages_names):
    model_paths = ""
    for package_name in packages_names:
        if model_paths != "":
            model_paths += pathsep

        package_path = get_package_prefix(package_name)
        model_path = join(package_path, "share")

        model_paths += model_path

    if 'GZ_SIM_RESOURCE_PATH' in environ:
        model_paths += pathsep + environ['GZ_SIM_RESOURCE_PATH']

    return model_paths

# Launch description
def generate_launch_description():
    moveit_config = MoveItConfigsBuilder("danieljr_armed", package_name="danieljr_armed_moveit_config").to_moveit_configs()
    declare_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description="use_sim_time simulation parameter"
    )
    model_path = ''
    resource_path = ''

    pkg_path = get_package_share_directory('danieljr_armed_description')
    model_path += join(pkg_path, 'models')
    resource_path += pkg_path + model_path

    if 'GZ_SIM_MODEL_PATH' in environ:
        model_path += pathsep+environ['GZ_SIM_MODEL_PATH']
    if 'GZ_SIM_RESOURCE_PATH' in environ:
        resource_path += pathsep+environ['GZ_SIM_RESOURCE_PATH']

    model_path = get_model_paths(['danieljr_armed_description'])

    robot_description_launcher = IncludeLaunchDescription(
       PathJoinSubstitution(
           [FindPackageShare("danieljr_armed_moveit_config"), "launch", "rsp.launch.py"]
       ),
    )

    start_gazebo_server_cmd = OpaqueFunction(function=start_gzserver)

    # TBD: RViz config and launching

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
    )

    # TBD: robot spawner 
    gazebo_spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-model",
            "danieljr_armed",
            "-topic",
            "robot_description",
            "-use_sim_time",
            "True"
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.0",
            "-R", "0.0",
            "-P", "0.0",
            "-Y", "3.14",
        ],
    )

    # Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='bridge_ros_gz',
        parameters=[
            {
                'config_file': join(
                    pkg_path, 'config', 'danieljr_armed_bridge.yaml'
                ),
                'use_sim_time': True,
            }
        ],
        output='screen',
    )

    # Image bridge
    gz_image_bridge_node = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=[
            "/camera_front/image",
            "/camera_scara/image"
        ],
        output="screen",
        parameters=[
            {'use_sim_time': True,
             'camera.image.compressed.jpeg_quality': 75},
        ],
    )

    # Twist stamped
    twist_stamped = Node(
        package="twist_stamper",
        executable="twist_stamper",
        name="twist_stamper",
        output="screen",
        parameters=[
            {
                "use_sim_time": True,
            }],
        remappings={('cmd_vel_out', '/danieljr_armed_base_control/cmd_vel'),
                    ('cmd_vel_in', '/cmd_vel')},
    )

    # Create the launch description
    ld = LaunchDescription()
    ld.add_action(SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', model_path))
    ld.add_action(SetEnvironmentVariable('GZ_SIM_MODEL_PATH', model_path))
    ld.add_action(robot_description_launcher)
    ld.add_action(declare_sim_time)
    ld.add_action(bridge)
    ld.add_action(gz_image_bridge_node)
    ld.add_action(start_gazebo_server_cmd)
    ld.add_action(rviz_node)
    ld.add_action(gazebo_spawn_robot)
    # TBD: RViz config and launching
    # TBD: robot spawner 
    ld.add_action(twist_stamped)
    return ld
