#!/usr/bin/env python3 
# Shebang line" specifies the interpreter. 

# imports --------------------
import cv2
import numpy as np
import signal
import sys
import json

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
    # Setup the video capture object
    # -------------------------------------------------------------------------
    cap = cv2.VideoCapture("docs/traffic.mp4")
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print('fps = ' + str(fps))

    # -------------------------------------------------------------------------
    # Read the frame
    # -------------------------------------------------------------------------
    ret, image_rgb = cap.read()

    win_name = 'Image'
    cv2.imshow(win_name, image_rgb) # Display the resulting frame


    # -------------------------------------------------------------------------
    # Define the BBox
    # -------------------------------------------------------------------------
    r = cv2.selectROI(win_name, image_rgb)
    print('ROI selected: ' + str(r))

    # create a dictionary to store the lane bounding box
    d_bboxes = {
        'lanes': []
        }

    d_bboxes['lanes'].append({
        'x': r[0],
        'y': r[1],
        'w': r[2],
        'h': r[3]
    })

    print('BBoxes: ' + str(d_bboxes))

    # Save the dict to a json
    filename = 'lane_bboxes.json'
    with open(filename,'w') as fp:
        json.dump(d_bboxes, fp, sort_keys=True, indent=4)
        print('Lane bounding boxes saved to ' + filename)

    # -------------------------------------------------------------------------
    # handle key press events
    # -------------------------------------------------------------------------
    # key = cv2.waitKey(0)

if __name__ == "__main__":
    main()




