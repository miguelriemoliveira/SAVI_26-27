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
    previous_is_significant_change = False
    number_of_cars = 0
    stamp_last_car_detected = 0
    threshold_blackout = 0.5 # secs

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


        # RISING EDGE Detect a car based on the rising edgoe
        if is_significant_change == True and previous_is_significant_change == False:
            is_rising_edge = True
            print(Fore.GREEN + Style.BRIGHT + 'Car detected!' + Style.RESET_ALL)
        else:
            is_rising_edge = False
            print(Style.DIM + 'no car ...' + Style.RESET_ALL)

        # FUSION, blackout + rising edge
        time_frame = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        time_since_last_car_detected =  round(time_frame - stamp_last_car_detected,1)
        if is_significant_change and time_since_last_car_detected > threshold_blackout \
            and is_rising_edge:
            is_car_detected = True
            print(Fore.GREEN + Style.BRIGHT + 'Car detected!' + Style.RESET_ALL)
        else:
            is_car_detected = False
            print(Style.DIM + 'no car ...' + Style.RESET_ALL)

        # Increment number of cars if a car is detected
        if is_car_detected:
            number_of_cars += 1
            stamp_last_car_detected = time_frame



        # Update the prev_ious_significant_change variable
        previous_is_significant_change = is_significant_change

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

        if is_significant_change:
            cv2.putText(image_gui, 'There is a change', (x, y-30), font, 1, (0, 0, 255), 2)

        if is_car_detected:
            cv2.putText(image_gui, 'There is a car', (x, y-55), font, 1, (0, 255, 0), 2)

        cv2.putText(image_gui, '#cars = ' +str(number_of_cars), (x, y-75), font, 1, (0, 255, 0), 2)

        cv2.putText(image_gui, 'Time since last detection = ' +str(time_since_last_car_detected), (x, y-105), font, 1, (0, 255, 0), 2)

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




