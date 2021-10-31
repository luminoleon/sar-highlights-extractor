from cutter import video_cutter
import os
import shutil
from typing import List, Tuple, Union

import cv2
import numpy as np


class auditory_analyzer:
    def __init__(self, file_path: str, ffmpeg_path: str = "ffmpeg", temp_dir: str = "tmp") -> None:
        self.file_path = file_path
        self.file_name = os.path.split(file_path)[1]
        self.ffmpeg_path = ffmpeg_path
        self.temp_dir = temp_dir
        self.temp_rms_log_path = "{}/{}_rms.txt".format(self.temp_dir, self.file_name)
        self.mkdir(self.temp_dir)
        
    def mkdir(self, path: str) -> None:
        if not os.path.exists(path):
            os.mkdir(path)

    def ffmpeg(self, command: str) -> None:
        os.system("{} {}".format(self.ffmpeg_path, command))

    def create_rms_log(self) -> None:
        with open(self.temp_rms_log_path, "w"):
            pass
        self.ffmpeg("-y -i {} -af astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file={} -f null -".format(self.file_path, self.temp_rms_log_path))

    def get_rms(self) -> List[List[float]]:
        self.create_rms_log()
        with open(self.temp_rms_log_path) as f:
            rms = []
            while True:
                try:
                    pts_time = float(f.readline().split()[2].split(":")[1])
                    rms_level = float(f.readline().split("=")[1])
                    rms.append([pts_time, rms_level])
                except IndexError:
                    break
        return rms
        
    def get_time_spans(self, rms_threshold: Union[int, float], max_gap: Union[int, float] = 3, margin: Union[int, float] = 3) -> None:
        rms = self.get_rms()
        filtered_pts_times = []
        for pts_time, rms_level in rms:
            if rms_level >= rms_threshold:
                filtered_pts_times.append(pts_time)
        time_spans = []
        i = 0
        time_span_start = filtered_pts_times[i]
        time_span_end = filtered_pts_times[i]
        while True:
            i += 1
            if i == len(filtered_pts_times):
                time_spans.append([time_span_start, filtered_pts_times[-1]])
                break
            if time_span_end + max_gap >= filtered_pts_times[i]:
                time_span_end = filtered_pts_times[i]
            else:
                time_spans.append([time_span_start, time_span_end])
                time_span_start = filtered_pts_times[i]
                time_span_end = filtered_pts_times[i]
        end_time = rms[-1][0]
        for i in range(len(time_spans)):
            if time_spans[i][0] - margin >= 0:
                time_spans[i][0] -= margin
            if time_spans[i][1] + margin <= end_time:
                time_spans[i][1] += margin
        return time_spans
    
    def clip(self, rms_threshold: Union[int, float], max_gap: Union[int, float] = 3, margin: Union[int, float] = 3, output_dir: str = "output") -> None:
        spans = self.get_time_spans(rms_threshold, max_gap, margin)
        video_cutter(self.file_path, output_dir).cut_all_by_seconds(spans)


class visual_analizer:
    def __init__(self, dir: str, templates_dir: str = "templates", output_dir: str = None, display_mode: bool = False, display_duration: int = 1) -> None:
        self.dir = dir
        self.cut_names = os.listdir(dir)
        template_names = os.listdir(templates_dir)
        templates = []
        for template_name in template_names:
            templates.append(cv2.imread("{}/{}".format(templates_dir, template_name)))
        self.templates = templates
        self.output_dir = output_dir
        self.display_mode = display_mode
        self.display_duration = display_duration
        if self.output_dir != None:
            if not os.path.exists(self.output_dir):
                os.mkdir(self.output_dir)

    def get_matching_rate(self, img: np.ndarray, templates: np.ndarray, roi: Tuple[int, int, int, int] = None):
        matching_rate = 0.0
        if roi != None:
            img = img[roi[1]:roi[3], roi[0]:roi[2], :]
        results = []
        for i in range(len(templates)):
            res = cv2.matchTemplate(img, templates[i], cv2.TM_CCOEFF_NORMED)
            results.append(res)
            max_val = cv2.minMaxLoc(res)[1]
            if max_val > matching_rate:
                matching_rate = max_val
        if self.display_mode:
            for i in range(len(templates)):
                cv2.namedWindow("Matching Result {}".format(i), cv2.WINDOW_FREERATIO)
                cv2.imshow("Matching Result {}".format(i), results[i])
            for i in range(len(templates)):
                cv2.namedWindow("Template {}".format(i))
                cv2.imshow("Template {}".format(i), templates[i])
            cv2.namedWindow("Image", cv2.WINDOW_FREERATIO)
            cv2.imshow("Image", img)
            cv2.waitKey(self.display_duration)
        return matching_rate
    
    def adaptive_canny(self, img_gray: np.ndarray, sigma: float = 0.33) -> np.ndarray:
        img_gray = cv2.cvtColor(img_gray, cv2.COLOR_BGR2GRAY)
        median_color = np.median(img_gray)
        threshold_1 = int(max(0, (1 - sigma) * median_color))
        threshold_2 = int(min(255, (1 + sigma) * median_color))
        edge = cv2.Canny(img_gray, threshold_1, threshold_2)
        return edge

    def canny(self, img_gray: np.ndarray, threshold: int) -> np.ndarray:
        img_gray = cv2.cvtColor(img_gray, cv2.COLOR_BGR2GRAY)
        threshold_1 = threshold
        threshold_2 = min(255, threshold * 2)
        edge = cv2.Canny(img_gray, threshold_1, threshold_2)
        return edge

    def is_matched(self, 
                   path: str, maching_threshold: float, 
                   matching_step: float = 1, 
                   roi: Tuple[int, int, int, int] = None, 
                   first_frame_only: bool = False, 
                   pre_process: str = None, 
                   binarization_threshold: int = None, 
                   canny_threshold: int = None) -> bool:
        capture = cv2.VideoCapture(path)
        fps = capture.get(cv2.CAP_PROP_FPS)
        frame_step = int(matching_step * fps)
        if frame_step < 1:
            frame_step = 1
        templates = []
        if pre_process == "binarization":
            for template in self.templates:
                template = cv2.threshold(template, binarization_threshold, 255, cv2.THRESH_BINARY)[1]
                templates.append(template)
        elif pre_process == "canny":
            for template in self.templates:
                template = self.canny(template, canny_threshold)
                templates.append(template)
        else:
            templates = self.templates
        if first_frame_only:
            frame = capture.read()[1]
            if pre_process == "binarization":
                frame = cv2.threshold(frame, binarization_threshold, 255, cv2.THRESH_BINARY)[1]
            elif pre_process == "canny":
                frame = self.canny(frame, canny_threshold)
            matching_rate = self.get_matching_rate(frame, templates, roi)
            print("Matching rate: {}".format("%.5f" % matching_rate))
            if matching_rate >= maching_threshold:
                capture.release()
                print("Matched.")
                return True
            else:
                print("Matching failed.")
                return False
        else:
            current_frame = 0
            while True:
                ret, frame = capture.read()
                if not ret:
                    capture.release()
                    break
                if current_frame % frame_step == 0:
                    if pre_process == "binarization":
                        frame = cv2.threshold(frame, binarization_threshold, 255, cv2.THRESH_BINARY)[1]
                    elif pre_process == "canny":
                        frame = self.canny(frame, canny_threshold)           
                    matching_rate = self.get_matching_rate(frame, templates, roi)
                    print("\rCurrent matching rate: {}".format("%.5f" % matching_rate), end="")
                    if matching_rate >= maching_threshold:
                            print("\nMatched.\n")
                            capture.release()
                            return True
                current_frame += 1
            print("\nMatching failed.\n")
        return False
    
    def pick(self, matching_threshold: float = 0.8, matching_step: float = 1, roi: Tuple[int, int, int, int] = None, first_frame_only: bool = False, pre_process: str = None, binarization_threshold: int = None, canny_threshold: int = None) -> None:
        for name in self.cut_names:
            path = self.dir + "/" + name
            print("Processing: {}".format(path))
            if self.is_matched(path, matching_threshold, matching_step, roi, first_frame_only, pre_process, binarization_threshold, canny_threshold):
                if self.output_dir != None:
                    shutil.move(path, self.output_dir)
