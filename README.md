# CICV
A Common Interface for OpenCV. **Easy to use** is my purpose.

# Install `CICV` Module
```bash
pip3 install cicv
```

# Sample Usage
```bash
# Image
python3 sample.py -i data/cat.jpg

# Video
python3 sample.py -i data/test.mp4

# RTSP
python3 sample.py -i rtsp://admin:admin@172.16.21.1:554/snl/live/1/1/n

# Images in Folder 
python3 sample.py -i data

# Camera
python3 sample.py -i /dev/video0

# Camera with custom resolution
python3 sample.py -i /dev/video0 -r 1920x1080

```
