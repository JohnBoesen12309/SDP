import launch
from launch.substitutions import Command, LaunchConfiguration
import launch_ros
import os
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = launch_ros.substitutions.FindPackageShare(package='red_robot_sdp').find('red_robot_sdp')
    default_model_path = os.path.join(pkg_share, 'src/description/red_robot_description.urdf')
    default_rviz_config_path = os.path.join(pkg_share, 'rviz/urdf_config.rviz')
    robot_localization_file_path = os.path.join(pkg_share, 'params/ekf_with_gps.yaml') 
    use_sim_time = LaunchConfiguration('use_sim_time')
    gps_params_file = os.path.join(pkg_share, 'params/ekf_params.yaml') #for using params from nav2 wiki

    robot_state_publisher_node = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': Command(['xacro ', LaunchConfiguration('model')])}]
    )
    joint_state_publisher_node = launch_ros.actions.Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        arguments=[default_model_path],
        condition=launch.conditions.UnlessCondition(LaunchConfiguration('gui'))
    )
    joint_state_publisher_gui_node = launch_ros.actions.Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        condition=launch.conditions.IfCondition(LaunchConfiguration('gui'))
    )
    rviz_node = launch_ros.actions.Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', LaunchConfiguration('rvizconfig')],
    )
    #nav2 wiki gps localization:
    start_ekf_filter_node_odom = launch_ros.actions.Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_filter_node_odom",
        output="screen",
        parameters=[gps_params_file, {"use_sim_time": True}],
        remappings=[("odometry/filtered", "odometry/local")]
    )
    start_ekf_filter_node_map = launch_ros.actions.Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_filter_node_map",
        output="screen",
        parameters=[gps_params_file, {"use_sim_time": True}],
        remappings=[("odometry/filtered", "odometry/global")]
    )
    start_robot_localization_node = launch_ros.actions.Node(
        package="robot_localization",
        executable="navsat_transform_node",
        name="navsat_transform",
        output="screen",
        parameters=[gps_params_file, {"use_sim_time": True}],
        remappings=[
            ("imu/data", "imu/data"),
            ("gps/fix", "gps/fix"),
            ("gps/filtered", "gps/filtered"),
            ("odometry/gps", "odometry/gps"),
            ("odometry/filtered", "odometry/global"),
        ]
    )
    
    #automatic gps localization:
    """
    start_navsat_transform_node = launch_ros.actions.Node(
        package='robot_localization',
        executable='navsat_transform_node',
        name='navsat_transform',
        output='screen',
        parameters=[robot_localization_file_path],
        remappings=[
        	    ('imu/data', 'imu/data'),
                    ('gps/fix', '/gps/fix'), 
                    ('gps/filtered', 'gps/filtered'),
                    ('odometry/gps', 'odometry/gps'),
                    ('odometry/filtered', 'odometry/global')
                    ]
    )
    # Start robot localization using an Extended Kalman filter...map->odom transform
    start_robot_localization_global_node = launch_ros.actions.Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node_map',
        output='screen',
        parameters=[robot_localization_file_path],
        remappings=[('odometry/filtered', 'odometry/global'), #add in comma for /set_pose
                    ('/set_pose', '/initialpose')
                    ]
    )

    # Start robot localization using an Extended Kalman filter...odom->base_footprint transform
    start_robot_localization_local_node = launch_ros.actions.Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node_odom',
        output='screen',
        parameters=[robot_localization_file_path],
        remappings=[('odometry/filtered', 'odometry/local'),
                    ('/set_pose', '/initialpose')
                    ]
    )
    """
    #rplidar_node launch
    rplidar_ros_node = launch_ros.actions.Node(
        package='rplidar_ros',
        executable='rplidar_composition',
        name='rplidar_composition',
        output='screen',
        parameters=[{
                'serial_port': '/dev/ttyUSB0',
                'serial_baudrate': 115200,  # A1 / A2
                #'serial_baudrate': 256000, # A3
                'frame_id': 'laser',
                'inverted': False,
                'angle_compensate': True,
                'scan_mode': 'Boost',
            }]
     )
     
    laser_odom_node = launch_ros.actions.Node(
        package='rf2o_laser_odometry',
        executable='rf2o_laser_odometry_node',
        name='rf2o_laser_odometry',
        output='log',
        parameters=[{
                    'laser_scan_topic' : '/scan',
                    'odom_topic' : '/odom',
                    'publish_tf' : True,
                    'base_frame_id' : 'base_link',
                    'odom_frame_id' : 'odom',
                    'init_pose_from_topic' : '',
                    'freq' : 20.0}]
     )



    return launch.LaunchDescription([
        launch.actions.DeclareLaunchArgument(name='gui', default_value='True',
                                            description='Flag to enable joint_state_publisher_gui'),
        launch.actions.DeclareLaunchArgument(name='model', default_value=default_model_path,
                                            description='Absolute path to robot urdf file'),
        launch.actions.DeclareLaunchArgument(name='rvizconfig', default_value=default_rviz_config_path,
                                            description='Absolute path to rviz config file'),
        joint_state_publisher_node,
        joint_state_publisher_gui_node,
        robot_state_publisher_node,
        rviz_node,
        #start_async_slam_toolbox_node,
        
        #start_navsat_transform_node,
        #start_robot_localization_local_node,
        #start_robot_localization_global_node,
        #start_ekf_filter_node_odom,
        #start_ekf_filter_node_map, 
        #start_robot_localization_node, 
        
        rplidar_ros_node,
        laser_odom_node,
       
    ])
