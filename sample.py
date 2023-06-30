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

    src = cicv.Source(      # initialize CICV source object
        input = args.input,
        resolution = args.resolution,
        fps = args.fps )
    
    stop_keys = [ ord('q'), ord('Q'), 27 ]      # define stop keyword
    fpser = FPS_HELPER()       # help to calculate FPS

    while(not cv2.waitKey(1) in stop_keys):

        frame = src.read()
        cicv.draw_text(frame, f'FPS:{fpser.get_fps()}')
        cv2.imshow('CICV Sample', frame)

    src.release()   # release source object

if __name__ == "__main__":
    main(get_args())