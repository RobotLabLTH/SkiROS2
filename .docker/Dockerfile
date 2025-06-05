# Dockerfile for SkiROS2 Development Environment

FROM ros:jazzy-ros-base AS skiros2_ws

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install apt dependencies.
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
    apt-utils curl fuse3 libfuse2 gdb nano \
    libegl1 libgl1-mesa-dev libglu1-mesa-dev '^libxcb.*-dev' libx11-xcb-dev \
    libxi-dev libxkbcommon-dev libxkbcommon-x11-dev libxrender-dev \
    libnss3 libasound2t64 libxkbfile1 \
    python3-pip python3-tk python3-wrapt python3-inflection \
    ros-jazzy-example-interfaces ros-jazzy-rqt-service-caller

# Create a ROS 2 workspace.
RUN mkdir -p /skiros2_ws/src/
COPY . /skiros2_ws/src/

WORKDIR /skiros2_ws

# Install external dependencies.
RUN source /opt/ros/jazzy/setup.bash && \
    apt-get update && \
    rosdep install --from-paths src -y --ignore-src

# Install SkiROS2 dependencies
RUN src/skiros2/scripts/install_fd_task_planner.sh

# Remove MatPlotLib display warnings.
RUN mkdir /tmp/runtime-root
ENV XDG_RUNTIME_DIR "/tmp/runtime-root"
RUN chmod -R 0700 /tmp/runtime-root
ENV NO_AT_BRIDGE 1

RUN apt-get update && \
apt-get install -y ros-jazzy-turtlesim && \
apt-get install -y '~nros-jazzy-rqt*'

# Set up the entrypoint.
CMD /bin/bash
COPY .docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]

RUN echo "source /entrypoint.sh && print_ros_variables" >> ~/.bashrc
