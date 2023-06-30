# Build from source ( recommand to use virtualenv )
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

