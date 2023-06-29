# CICV
A Common Interface for OpenCV.

# Support Input
|   Type        |   Describe
|   ---         |   ---
|   Image       |   Image file path.
|   Video       |   Video file path.
|   Directory   |   The directory has several images.
|   V4L2        |   Physical Camera.
|   RTSP        |   RTSP Streaming url.

# Install `CICV`
* `PyPI`
    ```bash
    pip3 install cicv
    ```
* Build from source ( recommand to use virtualenv )
    ```bash
    # Install virtualenv and wrapper
    $ sudo apt-get install python3-pip
    $ sudo pip3 install virtualenv
    $ sudo pip3 install virtualenvwrapper

    # Add into environment
    $ which virtualenvwrapper.sh
    $ vim ~/.bashrc

    # HEAD of ~/.bashrc
    export WORKON_HOME=~/.virtualenvs
    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
    # END of ~/.bashrc

    $ source ~/.bashrc

    # Activate Virtualenv
    $ mkvirtualenv cicv

    # Install opencv
    $ pip3 install opencv-python build
    ```

