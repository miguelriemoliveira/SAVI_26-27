#!/usr/bin/env python3 
# Shebang line" specifies the interpreter. 

# imports --------------------
import argparse
import cv2
import json
import numpy as np
import signal
import sys
from colorama import Fore, Style

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)


def signal_handler_term(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)


def showMask(window_name, image):
    image_to_show = image.astype(np.uint8)*255
    cv2.imshow(window_name, image_to_show)

# Main function
def main(): # this is our main function
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler_term)
    print("SAVI exercise")

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # initialize argparser
    ap = argparse.ArgumentParser()
    ap.add_argument("-lbf", "--lane_bboxes_filename", type=str, required=False, 
                    default='lane_bboxes.json',
                    help="Name of the json file containing the lane bounding boxes.", )
    ap.add_argument("-acr", "--average_color_reference", type=int, required=False, 
                    default=125,
                    help="Average reference color of the road")

    ap.add_argument("-dt", "--detection_threshold", type=int, required=False, 
                    default=40,
                    help="Detection threshold for deciding when a significant change occured.")

    args = ap.parse_args()
    args = vars(args) # transform the args into a dictionary
    print('Input args: ' + str(args))


    # Other setupds
    font = cv2.FONT_HERSHEY_SIMPLEX


    # read json file with the lane bounding boxes
    bboxes_filename = 'lane_bboxes.json'
    with open(bboxes_filename, "r") as f:
        d_bboxes = json.load(f)

    # Setup the video capture object -------------------------------------------
    cap = cv2.VideoCapture("docs/traffic.mp4")
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print('fps = ' + str(fps))

        # read json file with the lane bounding boxes
    with open(args['lane_bboxes_filename'], "r") as f:
        d_bboxes = json.load(f)

    # Setup the video capture object -------------------------------------------
    cap = cv2.VideoCapture("docs/traffic.mp4")
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print('fps = ' + str(fps))

    # -------------------------------------------------------------------------
    # Continuous operations
    # -------------------------------------------------------------------------
    while True:

        # -------------------------------------------------------------------------
        # Read the frame
        # -------------------------------------------------------------------------
        ret, image_rgb = cap.read()
        if not ret: # test to see if the video reading is finsished
            print('Completed processing video')
            break

        cv2.imshow('Image', image_rgb) # Display the resulting frame

        # -------------------------------------------------------------------------
        # How to detect the cars passing through tthe lanes
        # -------------------------------------------------------------------------
        # How many cars passed through lane X?

        image_gui = image_rgb.copy() # copy the image to draw the gui on it

        # Get the grayscale image for computing the average
        image_gray = cv2.cvtColor(image_rgb, cv2.COLOR_BGR2GRAY) # convert the image to gray scale


        # -------------------------------------------------------------------------
        # How to detect the cars passing through tthe lanes
        # -------------------------------------------------------------------------

        # Get the average grayscale color of the lane bounding box
        x = d_bboxes['lanes'][0]['x']
        y = d_bboxes['lanes'][0]['y']
        w = d_bboxes['lanes'][0]['w']
        h = d_bboxes['lanes'][0]['h']

        image_bbox = image_gray[y:y+h, x:x+w] # crop the image to the roi

        avg_color = round(np.mean(image_bbox),1) # compute the average color of the roi

        # TODO Guilherme suggest to theshold before ... 

        diff = abs(avg_color - args['average_color_reference'])

        is_significant_change = diff > args['detection_threshold']

        if is_significant_change:
            print(Fore.RED + Style.BRIGHT + 'There is a significant change' + Style.RESET_ALL)
        else:
            print(Style.DIM + 'Nothing new' + Style.RESET_ALL)

        # -------------------------------------------------------------------------
        # Visualization
        # -------------------------------------------------------------------------

        # Draw the bounding boxes of the lanes
        cv2.rectangle(image_gui, (x,y), (x+w, y+h), (255,0,0), 2)

        # draw the frame number and corresponding time
        frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        time_in_seconds = frame_number / fps
        cv2.putText(image_gui, f"Frame: {frame_number}, Time: {time_in_seconds:.2f}s", 
                    (40, 40), font, 1, (0, 255, 0), 2)


        # draw the avg color near the bbox
        cv2.putText(image_gui, 'Avg color = ' + str(avg_color), (x, y-10), font, 1, (255, 0, 0), 2)


        if is_significant_change:
            cv2.putText(image_gui, 'There is a change', (x, y-30), font, 1, (0, 0, 255), 2)


        # -------------------------------------------------------------------------
        # Visualization
        # -------------------------------------------------------------------------

        # Draw the bounding boxes of the lanes
        cv2.rectangle(image_gui, (x,y), (x+w, y+h), (255,0,0), 2)

        # draw the frame number and corresponding time
        frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        time_in_seconds = frame_number / fps
        cv2.putText(image_gui, f"Frame: {frame_number}, Time: {time_in_seconds:.2f}s", 
                    (40, 40), font, 1, (0, 255, 0), 2)


        # draw the avg color near the bbox
        cv2.putText(image_gui, 'Avg color = ' + str(avg_color), 
                    (x, y-10), font, 1, (255, 0, 0), 2)


        cv2.imshow('Image', image_gui) # Display the resulting frame

        # -------------------------------------------------------------------------
        # handle key press events
        # -------------------------------------------------------------------------
        key = cv2.waitKey(1000)
        if key == 113:
            print('Pressed q. Aborting ')
            break

if __name__ == "__main__":
    main()




