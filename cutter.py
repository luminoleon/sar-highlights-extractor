import os
import time
from typing import List, Union


class video_cutter:
    def __init__(self, file_path: str, output_dir: str = "output") -> None:
        self.file_path = file_path
        file_name = os.path.split(file_path)[1]
        self.file_name, self.file_extension = os.path.splitext(file_name)
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)
        
    def _get_timestamp(self) -> int:
        return int(time.time())

    def _get_time_length(self, time_start: str, time_end: str) -> None:
        time_start = time_start.split(":")
        seconds_start = int(time_start[0]) * 3600 + int(time_start[1]) * 60 + int(time_start[2])
        time_end = time_end.split(":")
        seconds_end = int(time_end[0]) * 3600 + int(time_end[1]) * 60 + int(time_end[2])
        seconds = seconds_end - seconds_start
        time_length = str(seconds // 3600).rjust(2, "0") + ":" + str(seconds % 3600 // 60).rjust(2, "0") + ":" + str(seconds % 3600 % 60).rjust(2, "0")
        return time_length
    
    def _generate_output_file_name(self, time_start: str, time_end: str) -> str:
        output_file_name = "{} {}-{}{}".format(self.file_name, time_start, time_end, self.file_extension).replace(":", ".")
        return output_file_name
    
    def _get_formatted_time(self, seconds: Union[int, float]) -> str:
        seconds = int(seconds)
        formatted_time = str(seconds // 3600).rjust(2, "0") + ":" + str(seconds % 3600 // 60).rjust(2, "0") + ":" + str(seconds % 3600 % 60).rjust(2, "0")
        return formatted_time
    
    def cut_one(self, time_start: str, time_end: str) -> None:
        time_length = self._get_time_length(time_start, time_end)
        os.system("ffmpeg -y -ss {} -t {} -i \"{}\" -codec copy -avoid_negative_ts 1 \"{}/{}\"".format(time_start, time_length, self.file_path, self.output_dir, self._generate_output_file_name(time_start, time_end)))
    
    def cut_all(self, time_spans: List[List[str]]) -> None:
        for time_start, time_end in time_spans:
            self.cut_one(time_start, time_end)
    
    def cut_one_by_seconds(self, time_start: Union[int, float], time_end: Union[int, float]) -> None:
        time_start = self._get_formatted_time(time_start)
        time_end = self._get_formatted_time(time_end)
        self.cut_one(time_start, time_end)
    
    def cut_all_by_seconds(self, time_spans: List[List[Union[int, float]]]) -> None:
        for time_start, time_end in time_spans:
            self.cut_one_by_seconds(time_start, time_end)
