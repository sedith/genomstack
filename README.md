# genom obelix

Small Python wrapper to configure and control GenoM components for Aerial Robots setup.

This assumes that the all robotpkg dependencies are installed and properly setup.

* Install in editable mode
    ```bash
    git clone https://github.com/sedith/genomstack.git
    cd genomstack
    pip install -e .
    ```
* Run the in python script or interactive shell as:
    ```python
    from genomstack import Robot

    r = Robot('tilthex_simu')

    r.setup()
    r.spin()
    r.start(prompt=True)

    r.goto(-5, 2, 3, 1, prompt=True)
    r.land(prompt=True)

    r.stop(prompt=True)
        
    ```


### TODOs

* script to run genom components running remotely on robot
* script for publishing to pom (lio relay)
* gz lidar and imu to test stuff in sim
