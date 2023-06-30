import cv2, time, logging, os, sys, threading, abc, copy
from typing import Tuple, Union, Literal
import numpy as np

from .utils import ( 
    limit_decor,
    InvalidInput,
    OpenError,
    ImageOpenError,
    VideoOpenError,
    UsbCamOpenError,
    RtspOpenError,
    get_extension,
    check_input_ext,
    check_file_exists,
    check_folder_exists,
    check_image_buffer
)

from .config import (
    WAIT_RTSP_TIME,
    IMAGE_EXTS,
    VIDEO_EXTS,
    RTSP_EXTS,
    IMAGE,
    DIR,
    VIDEO,
    RTSP,
    CAM
)

# --------------------------------------------------
# Basic Wrapper
class Wrapper(abc.ABC):

    @abc.abstractclassmethod
    def read(self) -> np.ndarray:
        """Read frame via opencv.

        Returns:
            np.ndarray: frame buffer
        """
        pass

    @abc.abstractclassmethod
    def get_type(self) -> str:
        """Get the type of the current object.

        Returns:
            str: _description_
        """
        raise NotImplementedError

    @abc.abstractclassmethod
    def get_fps(self):
        raise NotImplementedError

    @abc.abstractclassmethod
    def release(self):
        raise NotImplementedError

    def _init_time_params(self):
        self.timeout = 1/self.get_fps()
        self.t_prev = time.time()
        self.t_bias = 1e-5
    
    def _wait_time(self):
        # NOTE: Sleep Directly for correct FPS 
        t_process = ( self.timeout - (time.time() - self.t_prev ) )
        if t_process > 0:
            time.sleep( t_process )
        self.t_prev = time.time()

# --------------------------------------------------
# Source Wrapper Object

class ImageWrapper(Wrapper):
    
    def __init__(self, path:str) -> None:
        
        # Checking
        check_file_exists(file_path=path)
        check_input_ext(input=path, sup_ext=IMAGE.exts)

        # Parameters
        self.path = path
        self.frame = check_image_buffer(cv2.imread(path))
        
        # Time Parameters
        self._init_time_params()

    def read(self):

        # Copy
        _frame = copy.deepcopy(self.frame)

        # Wait for correct fps
        self._wait_time()

        return _frame 
    
    def get_type(self):
        return IMAGE.__name__

    def get_fps(self):
        return IMAGE.fps
    
    def release(self):
        self.frame = None

class DirImageWrapper(ImageWrapper):

    def __init__(self, path ) -> None:

        # Checking
        check_folder_exists(path)

        # Parameters
        self.path = path
        self.img_id = -1
        
        self.img_paths = []
        self.img_buffers = []
        self.img_nums = 0

        # Collect all images
        for img in os.listdir(path):
            
            # get path and check extension
            img_path = os.path.join(path, img)
            if not ( get_extension(img_path) in IMAGE.exts ):
                continue
            
            # check image buf
            img_buf = cv2.imread(img_path)
            check_image_buffer(img_buf)
            
            # collect image path and buffer
            self.img_paths.append(img_path)
            self.img_buffers.append(img_buf)
        
        # Log
        logging.info('Found {} images in {}'.format(len(self.img_paths), self.path))

        # Time Parameters
        self._init_time_params()

    def read(self):

        self.img_nums += 1

        self.img_id += 1
        if self.img_id > len(self.img_paths)-1:
            self.img_id = 0

        self.img_nums = 0

        # Copy
        _frame = copy.deepcopy(self.img_buffers[self.img_id])

        # Wait for correct fps
        self._wait_time()

        return _frame

    def get_type(self):
        return DIR.__name__
    
    def release(self):
        self.img_paths, self.img_buffers = [], []

class VideoWrapper(Wrapper):

    def __init__(self, path) -> None:

        if not os.path.isfile(path):
            raise InvalidInput(f"Can not find the video from {path}")
        
        check_input_ext(path, VIDEO_EXTS)

        # Init
        self.path = path
        self.cap = cv2.VideoCapture()
        self.set_cap()

        self._init_time_params()
        
    def set_cap(self):
        status = self.cap.open(self.path)
        if not status:
            raise VideoOpenError(f"Can not open the {self.get_type} from {self.path}")

    def reset_cap(self):
        logging.debug('Reset Source')
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def read(self):

        # Read Video Capture
        status, frame = self.cap.read()

        if not status:
            self.reset_cap()
            status, frame = self.cap.read()
            if not status:
                raise VideoOpenError(f"VideoWrapper is broken, can't get the frame from {self.path}")
        
        self._wait_time()
        
        return frame
    
    def get_fps(self):
        try:
            return self.cap.get(cv2.CAP_PROP_FPS)
        except Exception as e:
            raise RuntimeError('Can not get FPS value')

    def get_type(self):
        return VIDEO.__name__

    def get_delay_time(self):
        return self.frame_delay

    def release(self):
        self.cap.release()

@limit_decor(WAIT_RTSP_TIME)
def get_rtsp_cap(rtsp):
    capture = cv2.VideoCapture(rtsp)
    return (True, capture)

class RtspWrapper(VideoWrapper):

    def __init__(self, path) -> None:
        
        # Init
        self.path = path

        check_fmt = False
        for fmt in RTSP_EXTS:
            if fmt in path:
                check_fmt = True
        if not check_fmt:
            raise InvalidInput("Can not find the rtsp:// in input.")

        self.set_cap()

    def set_cap(self):
        # Define Error Message
        error_message = f"Can not open RTSP stream, make sure the uri is available ({self.path})"

        # Get RTSP VideoCapture
        status, self.cap = get_rtsp_cap(self.path)

        # Check RTSP is available
        if not status:
            raise RtspOpenError(error_message)

        # Check RTSP is not empty
        if not self.cap.read()[0]:
            raise RtspOpenError(error_message)

    def reset_cap(self):
        logging.warning('Reset Camera')
        self.set_cap()
        time.sleep(1/30)

    def read(self):
        status, frame = self.cap.read()
        
        if not status:
            self.reset_cap()
            
        return frame

    def get_type(self):
        return RTSP.__name__

class UsbCameraWrapper(VideoWrapper):
    
    def __init__(self, path, resolution, fps) -> None:

        self.path = path
        
        self.cap = cv2.VideoCapture()
        self.fps = RTSP.fps if fps is None else fps
        self.resolution = resolution
        self.set_cap(self.resolution, self.fps)

    def set_cap(self, resolution, fps):
        """ Setup camera 
        - Args
            - resolution: A tuple with width and height, e.g.( <width>, <height> )
            - fps: The fps 
        """
        if not isinstance(self.path, int) and self.path.isdigit():
            self.path = int(self.path)

        try:

            status = self.cap.open(self.path)
            if not status:
                raise OpenError("Can not open the camera from {}".format(self.path))
            
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 4.0)
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            
            if resolution:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
            if fps:
                self.cap.set(cv2.CAP_PROP_FPS, fps)
            
        except ValueError:
            raise InvalidInput("Can not find the camera {}".format(self.path))

    def get_type(self):
        return CAM.__name__

    def reset_cap(self):
        self.set_cap(self.resolution, self.fps)
        logging.debug('Reset Camera')
        time.sleep(1/30)

    def read(self):
        status, frame = self.cap.read()
        
        if not status:
            self.reset_cap()    
            status, frame = self.cap.read()
            
            if not status:
                raise UsbCamOpenError("Can not capture frame, please make sure the camera is available")
        
        return frame
    
    def get_fps(self):
        return self.fps

# --------------------------------------------------
# Entrance

def get_source_object(input:str, camera_resolution:Tuple[int, int]=(1280, 720), fps:int=30) -> Wrapper:
    """Trying to instance the source object

    Args:
        input (str): input data
        camera_resolution (Tuple[int, int], optional): setup camera resolution ( width, height ) if need. Defaults to (1280, 720).
        fps (int, optional): setup fps if need. Defaults to 30.

    Raises:
        errors: the latest exception

    Returns:
        Wrapper: return a iVIT Source Wrapper
    """
    errors = []
    for reader in (ImageWrapper, DirImageWrapper, VideoWrapper, RtspWrapper):
        try:
            return reader(input)
        except (InvalidInput, OpenError) as e:
            errors.append(e)

    try:
        return UsbCameraWrapper(input, camera_resolution, fps)
    except (InvalidInput, OpenError) as e:
        if len(errors)==0:
            errors.append(e)
    
    # if not errors[OpenError]:
    #     logging.error(*errors[InvalidInput])#, file=sys.stderr, sep='\n')
    # else:
    #     logging.error(*errors[OpenError])#, file=sys.stderr, sep='\n')

    raise errors[-1]

class Source(object):

    def __init__(self, input:str, resolution:Tuple[int, int]=None, fps:int=None) -> None:
        """iVIT Source Object
        
        Args:
            input (str): the input data, supported image path, image folder, 
            video path, rtsp uri and usb camera
            resolution (Tuple[int, int], optional): A tuple value with width and height, 
            you will get target size of the frame after setting up. Defaults to None.
            fps (int, optional): This option is only for camera. Defaults to None.
        """
        self.input = input
        self.src = get_source_object(input, resolution, fps)

        # Init
        self.frame = self.src.read()
        self.height, self.width = self.frame.shape[:2]
        self._print_info()

    def _print_info(self):
        print(
            "[ iVIT Source Information ]\n",
            f"\t- Name      : {self.input}\n",
            f"\t- Type      : {self.src.get_type()}\n",
            f"\t- Shape     : {self.width}, {self.height} ( W, H )\n",
            f"\t- FPS       : {self.src.get_fps()}\n"
        )

    def read(self) -> np.ndarray:
        """ Return the OpenCV::Mat """
        return self.src.read()
    
    def set_cam(self, width:int=1280, height:int=720, fps:int=30) -> None:      
        """Setup camera resolution and reload source object which only support usb camera mode.

        Args:
            width (int, optional): camera width. Defaults to 1280.
            height (int, optional): camera height. Defaults to 720.
            fps (int, optional): camera fps. Defaults to 30.
        """
        if self.src.get_type() != CAM:  # Only Camera can use set_cam function 
            return   

        self.src.set_cap(                   # Reload Source Object with new width, height and fps
            resolution = (width, height),
            fps = fps )

        logging.warning("Reset Camera")

    def get_fps(self)->float:
        """Get source fps value

        Returns:
            float: frame per second
        """
        return self.src.get_fps()
    
    def get_type(self)->Literal["IMAGE", "VIDEO", "DIR", "CAM", "RTSP"]:
        """Get source type

        Returns:
            str: source type
        """
        return self.src.get_type()

    def get_shape(self) -> Tuple[int, int]:
        """Get source shape (height, width)

        Returns:
            tuple: (height, width)
        """
        return ( self.height, self.width )
    
    def release(self) -> None:
        """Release source object """
        return self.src.release()

class SourceV2(object):

    def __init__(self, input:str, resolution:Tuple[int, int]=None, fps:int=None, start:bool=False) -> None:
        """iVIT Source Object ( Async )

        Args:
            input (str): the input data, supported image path, image folder, video path, rtsp uri and usb camera.
            resolution (Tuple[int, int], optional): A tuple value with width and height, you will get target size of the frame after setting up. Defaults to None.
            fps (int, optional): This option is only for camera. Defaults to None.
            start (bool, optional): Start the source piepline after instance. Defaults to False.

        Notes:
            1. Keep update the newest frame
            2. Keep loop in background
            3. Auto reload source
        """
        self.input = input
        self.src = get_source_object(input, resolution, fps)

        self.frame = None
        self.cur_frame_id = 0
        self.pre_frame_id = 0

        self.height = None
        self.width = None

        self.is_ready = True
        self.t_update = time.time()
        self.t_warnup = 0

        # Errors
        self.errors = []

        # Init
        self.frame = self.src.read()
        self.height, self.width = self.frame.shape[:2]
        self._print_info()
        
        self.t = self._create_thread()  # Create Thread and start ( if need )
        if start: self.start()

    def _print_info(self):
        print(
            "[ iVIT Source Information ]\n",
            f"\t- Name      : {self.input}\n",
            f"\t- Type      : {self.src.get_type()}\n",
            f"\t- Shape     : {self.width}, {self.height} ( W, H )\n",
            f"\t- FPS       : {self.src.get_fps()}\n",
            f"\t- WARNUP    : {self.t_warnup}s\n"
        )

    def _create_thread(self) -> threading.Thread:
        """ Create main thread: which keeping update the frame variable """
        t = threading.Thread( 
            target = self._keep_update_frame, 
            daemon = True )
        time.sleep(0.33)
        return t

    def _keep_update_frame(self):
        """ Keep updating current frame in background thread. """

        # NOTE: Legacy Version
        # -------------------------------
        # timeout = 1/self.src.get_fps()
        # t_cur = time.time()
        # -------------------------------
        
        try:
            while( self.is_ready ):

                self.frame = self.src.read()
                if self.frame is None: break
                self.cur_frame_id += 1

                # NOTE: Legacy Version
                # -------------------------------
                # t_start = time.time()

                # # Read data
                # self.frame = self.src.read()
                
                # if self.frame is None: break

                # # Update frame index
                # self.cur_frame_id += 1

                # # Calculate Time
                # t_cur = time.time() - t_start
                # t_delay = timeout - t_cur
                # if t_delay > 0:
                #     time.sleep( t_delay )
                # -------------------------------

        except Exception as e:
            logging.exception(e)
            self.errors.append(e)
            
        finally:            
            self._stop_params()
            self.src.release()
            
    def _wait_thread(self, stop_thread=False):
        while(self.t.is_alive() if stop_thread else not self.t.is_alive()):
            print('\rWait thread {} ...'.format(
                "Stoped" if stop_thread else "Launch"
            ), end='')
            time.sleep(0.33)
        return
    
    def _wait_frame(self, warnup:int=10):
        """ Wait available frame """
        
        # Helper
        wait = lambda x=33e-3: time.sleep(x)

        t = time.time()
        while(self.frame is None):  # wait available frame 
            self.t_warnup = round(time.time()-t, 3)
            print(f'Wait Available Frame ... {self.t_warnup}s', end='\r');
            wait()
        
        print()
        while(self.src.get_type() == CAM and self.cur_frame_id < warnup):   # wait camera frame    
            self.t_warnup = round(time.time()-t, 3)
            print(f'Camera White Balance Warnup ... {self.cur_frame_id+1}/{warnup}', end='\r')
            wait()
        
        if None in ( self.height, self.width):
            self.height, self.width = self.frame.shape[:2]
            
        print('\n')

    def _stop_params(self):
        self.is_ready = False 

    def _stop_thread(self):
        if self.t.is_alive():
            self.t.join()
            self._wait_thread(stop_thread=True)

    def set_cam(self, width:int=1280, height:int=720, fps:int=30) -> None:      
        """Setup camera resolution and reload source object which only support usb camera mode.

        Args:
            width (int, optional): camera width. Defaults to 1280.
            height (int, optional): camera height. Defaults to 720.
            fps (int, optional): camera fps. Defaults to 30.
        """        
        if self.src.get_type() != CAM:  # Only Camera can use set_cam function 
            return   

        self.src.set_cap(                   # Reload Source Object with new width, height and fps
            resolution = (width, height),
            fps = fps )

        logging.warning("Reset Camera")

             
    def start(self) -> threading.Thread:
        """Start the source thread.

        Returns:
            threading.Thread: inference thread object

        Workflow:
            1. Wait Thread launch.
            2. Wait Camera warnup if need.
            3. Set `is_ready = True`

        """
        
        if self.t is None: 
            self.t = self._create_thread()
        
        if self.t.is_alive():
            logging.info(f'The source thread is already started ! ( {self.get_thread_id()} )')
        else:
            self.t.start()
            logging.info(f"Start the source thread ! ( {self.get_thread_id()} )")
        
        self._wait_thread()
        self._wait_frame()
        self.is_ready = True
        return self.t

    def release(self) -> None:
        """ Close Thread and release Capture Object """
        self._stop_params()
        self._stop_thread()
        self.src.release()

    def get_thread_id(self) -> int: 
        """Get threading.Thrad.ident

        Returns:
            int: threading pid
        """
        return self.t.ident

    def get_fps(self) -> int:
        """Get source fps value

        Returns:
            int: frame per second
        """
        return self.src.get_fps()
    
    def get_type(self)->Literal["IMAGE", "VIDEO", "DIR", "CAM", "RTSP"]:
        """Get source type

        Returns:
            str: source type
        """
        return self.src.get_type()

    def get_shape(self) -> Tuple[int, int]:
        """Get source shape (height, width)

        Returns:
            tuple: (height, width)
        """
        return ( self.height, self.width )

    def read(self) -> Tuple[bool, np.ndarray ]:
        """ Get source status and current frame """

        if not self.is_ready:
            raise RuntimeError('iVIT Source has not start yet.')

        # Check current frame and previous frame
        if self.pre_frame_id == self.cur_frame_id:    
            return (False, self.frame)
        
        self.pre_frame_id = self.cur_frame_id
        self.t_update = time.time()
        return (True, self.frame)
