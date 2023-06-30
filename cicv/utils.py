import time, threading, os, sys
import numpy as np
import cv2

# --------------------------------------------------
# Decorator to limit the actual request time or function execution time

class Timeout(threading.Thread):

    def __init__(self, target, args=()):
        super(Timeout, self).__init__()
        self.func = target
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception:
            return None

def limit_decor(limit_time):
    """
    - param limit_time: 
        Set the maximum allowable execution time, unit: second
    
    - return: 
        Untimed returns the value of the decorated function; timed out returns None
    """
    def functions(func):
        def run(*params):
            thre_func = Timeout(target=func, args=params)
            # The thread method terminates when the main thread terminates (exceeds its length)
            thre_func.setDaemon(True)
            thre_func.start()
            # Count the number of segmental slumbers
            sleep_num = int(limit_time // 1)
            sleep_nums = round(limit_time % 1, 1)
            # Sleep briefly several times and try to get the return value
            for i in range(sleep_num):
                time.sleep(1)
                infor = thre_func.get_result()
                if infor:
                    return infor
            time.sleep(sleep_nums)
            # Final return value (whether or not the thread has terminated)
            if thre_func.get_result():
                return thre_func.get_result()
            else:
                return (False, None)  # Timeout returns can be customized

        return run

    return functions

# --------------------------------------------------
# Custom Exception

class InvalidInput(Exception):

    def __init__(self, message):
        self.message = message

class OpenError(Exception):

    def __init__(self, message):
        self.message = message

class ImageOpenError(Exception):

    def __init__(self, message):
        self.message = message

class VideoOpenError(Exception):

    def __init__(self, message):
        self.message = message

class UsbCamOpenError(Exception):

    def __init__(self, message):
        self.message = message

class RtspOpenError(Exception):

    def __init__(self, message):
        self.message = message

# --------------------------------------------------
# Helper function

def get_extension(path:str) -> str:
    """Get Extension with lowercase"""
    return os.path.splitext(path)[1].replace('.', '').lower()

def check_input_ext(input:str, sup_ext:list) -> None:
    """Check input extension is correct

    Args:
        input (str): input information
        sup_ext (list): support extension

    Raises:
        InvalidInput: unexpect extension
    """

    input_ext = get_extension(input)
    if input_ext in sup_ext: 
        return
    raise InvalidInput(f"Get unexcepted extension: {input_ext}, support is {sup_ext}")

def check_file_exists(file_path:str) -> None:
    """Check file exist or raise the expection: InvalidInput"""
    if os.path.isfile(file_path):
        return
    raise InvalidInput(f"Can not find the image ({file_path})")

def check_folder_exists(folder_path:str) -> None:
    """Check folder exist or raise the expection: InvalidInput"""
    if os.path.isdir(folder_path):
        return
    raise InvalidInput(f"Can not find the folder ({folder_path})")

def check_image_buffer(frame:np.ndarray) -> np.ndarray:
    if frame is None:
        raise ImageOpenError("Get empty image")
    return frame

def draw_text(
        frame:np.ndarray, 
        message:str, 
        position:tuple=(40,40), 
        font_face=cv2.FONT_HERSHEY_SIMPLEX, 
        font_scale=1, 
        color=(0, 255, 0), 
        thickness=2) -> None:
    """Draw hightlighted text"""
    cv2.putText(frame, message, position, font_face, font_scale, (255, 255, 255), thickness + 1) # white border
    cv2.putText(frame, message, position, font_face, font_scale, color, thickness)
