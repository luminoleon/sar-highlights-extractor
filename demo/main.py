import os
import sys

sys.path.append("..")

current_work_dir = os.path.dirname(__file__)
if current_work_dir != "demo":
    os.chdir("demo")

import analizer

if __name__ == "__main__":
    analizer.auditory_analyzer("demo_material.mp4").clip(rms_threshold=-18, output_dir="step_1")
    analizer.visual_analizer(
        dir="step_1", 
        templates_dir="templates/tips", 
        output_dir="step_2", 
        display_mode=True,
        display_duration=500
    ).pick(
        matching_threshold=0.65, 
        pre_process="binarization", 
        binarization_threshold=200
    )
    analizer.visual_analizer(
        dir="step_2", 
        templates_dir="templates/weapons", 
        output_dir="output", 
        display_mode=True,
        display_duration=500
    ).pick(
        matching_threshold=0.7, 
        first_frame_only=True, 
        roi=(1500, 950, 1920, 1080)
    )
