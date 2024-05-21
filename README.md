# Gym Tracker Application

## Overview

The Gym Tracker application is designed to help users track objects in gym workout videos. The application allows users to open a video, play, pause, and track the movement of selected objects (e.g., dumbbells). The tracked movement is displayed in real-time, and users can save the tracked video. The application also includes functionality to switch back to the original video.

## Features

- **Open Video**: Load a video file for tracking.
- **Play/Pause**: Control video playback.
- **Track Object**: Select an object in the video to track its movement.
- **Save Tracked Video**: Save the tracked video to a chosen location.
- **Back to Original Video**: Switch back to the original video without tracking.

## Requirements

- Python 3.x
- PyQt5
- OpenCV
- NumPy
- Matplotlib

## Installation

1. **Clone the repository**:
   ```sh
   git clone https://github.com/your-username/gym-tracker.git
   cd gym-tracker
   ```
2. **Create a virtual environment**:
    ```sh
    python -m venv gym_tracker_env
    source gym_tracker_env/bin/activate  # On Windows use: gym_tracker_env\Scripts\activate
    ```
3. **Install the dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. **Run the application**:

    ```sh
    python main.py
    ```

2. **Open a Video**:
    - Click on the "Open Video" button and select a video file to load.

3. **Play/Pause Video**:
    - Use the "Play" button to start the video and the "Pause" button to stop it.

4. **Track Object**:
    - Click on the "Track Object" button.
    - Select the object in the video by dragging a rectangle around it.
    - The application will track the movement of the selected object.

5. **Save Tracked Video**:
    - Click on the "Save" button to save the tracked video to your desired location.

6. **Back to Original Video**:
    - Click on the "Back to Original Video" button to return to the original untracked video.

## Project Structure

    ```graphql
    gym-tracker/
    │
    ├── main.py                # Entry point for the application
    ├── video_player.py        # Contains the VideoPlayer class
    ├── object_tracker.py      # Contains the ObjectTracker, ROISelector, and TrackingWindow classes
    ├── utils.py               # Utility functions
    ├── requirements.txt       # Project dependencies
    └── icons/                 # Icons for the application
        ├── play.png
        └── pause.png

    ```