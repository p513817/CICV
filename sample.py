import sys, os, cv2, time
import argparse
import cicv

class FPS_HELPER():
    def __init__(self) -> None:
        self.prev_time = time.time()
        self.cur_fps = 0

    def get_fps(self) -> int:
        self.cur_fps = 1//(time.time() - self.prev_time)
        self.prev_time = time.time()
        return self.cur_fps

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', default='ivit', help="The cv window name.")
    parser.add_argument('-i', '--input', required=True, help="The input data.")
    parser.add_argument('-r', '--resolution', type=str, default=None, help="The resolution ( e.g. {w}x{h} ) you want to get from source object. only support V4L2 type")
    parser.add_argument('-f', '--fps', type=int, default=None, help="The fps you want.")
    args = parser.parse_args()
    if args.resolution:
        args.resolution = tuple(map(int, args.resolution.split('x')))
    return args

def main(args:argparse.Namespace):

    # Initialize CICV Source Object
    src = cicv.Source(
        input = args.input,
        resolution = args.resolution,
        fps = args.fps )
    
    # Set Variable
    stop_stream = False
    stop_keys = [ ord('q'), ord('Q'), 27 ]
    fps_helper = FPS_HELPER()

    while(not stop_stream):

        # Get frame
        frame = src.read()

        # Draw FPS and Display 
        cicv.put_highlighted_text(frame=frame, message=f'FPS:{fps_helper.get_fps()}')
        cv2.imshow('CICV Sample', frame)
        stop_stream = (cv2.waitKey(1) in stop_keys)

    # Release Source Object
    src.release()

if __name__ == "__main__":
    main(get_args())