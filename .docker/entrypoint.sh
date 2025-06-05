#!/bin/bash

# Source ROS and the deliberation workspace.
source /opt/ros/jazzy/setup.bash

# Ignores additional output because of deprecated Python tooling in ament_python
export PYTHONWARNINGS="ignore:setup.py install is deprecated,ignore:easy_install command is deprecated"

export ROS_WS=/skiros2_ws

# Convenience functions
function ws() {
        cd ${ROS_WS}
}

function skiros2_src() {
        cd ${ROS_WS}/src
}

function print_ros_variables () {
        echo -e "ROS Distro: \t" ${ROS_DISTRO}
        echo -e "ROS Domain ID: \t" ${ROS_DOMAIN_ID}
        echo -e "ROS Workspace: \t" ${ROS_WS}
}

function skiros2_build() {
        cwd=$(pwd)
        ws
        colcon build --symlink-install --continue-on-error --mixin compile-commands
        cd ${cwd}
}

function skiros2_build_packages() {
        cwd=$(pwd)
        ws
        colcon build --symlink-install --continue-on-error --mixin compile-commands --packages-select "$@"
        cd ${cwd}
}

function skiros2_build_packages_up_to() {
        cwd=$(pwd)
        ws
        colcon build --symlink-install --continue-on-error --mixin compile-commands --packages-up-to "$@"
        cd ${cwd}
}

function skiros2_clean () {
        cwd=$(pwd)
        ws
        local _ret=$?
        if [ $_ret -ne 0 ] ; then
                echo "Could not switch dirs. Aborting delib_clean"
                return $_ret
        fi
        rm -r build/*
        rm -r install/*
        rm -r log/*
        cd ${cwd}
}

# Use this to switch to software rendering to avoid
# conflicts with GPU and docker
function qt_soft_render() {
        export QT_QUICK_BACKEND=software
        echo "Using ${QT_QUICK_BACKEND} for QT rendering"
}

# Automatic build when entering the container
if [ ! -f ${ROS_WS}/install/setup.bash ]
then
  skiros2_build
fi
source ${ROS_WS}/install/setup.bash

# Execute the command passed into this entrypoint.
exec "$@"
