# --------------------------------------------------
# Constant Variable
IMAGE_EXTS   = [ 'jpg', 'jpeg', 'png', 'tiff', 'tif', 'bmp' ]
VIDEO_EXTS   = [ 'mp4', 'avi', 'mov', 'wmv' ]
RTSP_EXTS    = [ 'rtsp://' ]

# IMAGE   = "IMAGE"
# VIDEO   = "VIDEO"
# DIR     = "DIR"
# CAM     = "CAM"
# RTSP    = "RTSP"

WAIT_RTSP_TIME = 3

class IMAGE:
    fps = 30.0
    exts = [ "jpg", "jpeg", "png", "tiff", "tif", "bmp" ]

class DIR:
    fps = 30.0
    exts = [ ]

class VIDEO:
    fps = None
    exts = [ "mp4", "avi", "mov", "wmv" ]

class RTSP:
    fps = 30.0
    exts = [ "rtsp://" ]

class CAM:
    fps = 30.0
    exts = [ "video" ]