import os
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从视频素材中截图。")
    parser.add_argument("path", type=str, help="视频文件路径")
    parser.add_argument("time", type=str, help="截图时间位置，格式为HH:MM:SS")
    args = parser.parse_args()
    os.system("ffmpeg -ss {} -i {} -frames:v 1 screenshot.png".format(args.time, args.path))
    