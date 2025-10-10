# videotoPDF
Convert video to PDF

Adjusting Settings

similarity_threshold (0.90-0.98 recommended):

0.90 = More slides captured (catches subtle changes)
0.98 = Fewer slides (only major changes)


sample_rate:

1 = Check every frame (slowest, most accurate)
30 = Check once per second for 30fps video (good balance)
60 = Check every 2 seconds (faster, may miss quick slides)



For Box/Recorded Lectures
If you're downloading from Box:

Download the video file first
Point video_path to the downloaded file
Run the script

Tips for Best Results

Screen recordings: Use similarity_threshold=0.95
Camera recordings: May need lower threshold (~0.90) due to motion
Fast-paced lectures: Use lower sample_rate (e.g., 15)
Slow lectures: Use higher sample_rate (e.g., 60) for faster processing

The script will print progress and let you know how many unique slides it found!RetryClaude does not have the ability to run the code it generates yet.Claude can make mistakes. Please double-check responses.
