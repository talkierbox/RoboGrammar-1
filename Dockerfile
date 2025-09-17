FROM ubuntu:18.04

# Install APT packages
RUN apt-get update && apt-get install -y cmake libglew-dev xorg-dev python3 python3-pip python3-dev libjpeg-dev zlib1g-dev

# Upgrade pip and install build tools
RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install cython

# Set PYTHONPATH
ENV PYTHONIOENCODING=utf-8
ENV PYTHONPATH="/robot_design/examples/design_search:/robot_design/examples/graph_learning:/robot_design/build/examples/python_bindings:$PYTHONPATH"

# Install third party Python packages
RUN pip3 install numpy==1.19.5
RUN pip3 install numpy-quaternion==2020.11.2.17.0.49
RUN pip3 install scipy
RUN pip3 install torch
RUN pip3 install pillow
RUN pip3 install matplotlib
RUN pip3 install pandas
RUN pip3 install seaborn
RUN pip3 install flask

# Copy our code and build
WORKDIR /robot_design
COPY . .
WORKDIR /robot_design/build
RUN cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo ..
RUN make -j8

WORKDIR /robot_design

# Set environment variable for data directory
ENV ROBOT_DESIGN_DATA_DIR=/robot_design/data/

# Expose API port
EXPOSE 5555

# Default command - start the API server
CMD ["python3", "examples/design_search/api.py"]