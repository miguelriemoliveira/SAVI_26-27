#!/usr/bin/env python3 
# Shebang line" specifies the interpreter. 

# imports --------------------
import cv2
import numpy as np

def showMask(window_name, image):
    image_to_show = image.astype(np.uint8)*255
    cv2.imshow(window_name, image_to_show)

# Main function
def main(): # this is our main function
    print("SAVI exercise")

    # -------------------------------------------------------------------------
    # Setup the video capture object
    # -------------------------------------------------------------------------
    cap = cv2.VideoCapture("docs/traffic.mp4")
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print('fps = ' + str(fps))


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
        # Colors of the cars 



        # -------------------------------------------------------------------------
        # handle key press events
        # -------------------------------------------------------------------------
        key = cv2.waitKey(1000)
        if key == 113:
            print('Pressed q. Aborting ')
            break

if __name__ == "__main__":
    main()




