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

    # relative path
    image = cv2.imread("images/dog_2.jpg")
    height, width, channels = image.shape
    image = cv2.resize(image, (round(width/2), round(height/2) ))
    cv2.imshow('Original', image)
    H,W,NC = image.shape

    # --------------------------------
    # Segment green color to isolate the grass 
    # --------------------------------

    # conversion to hsv color model
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # split of the color channels
    h, s, v = cv2.split(hsv_image)
    cv2.imshow('H', h)
    cv2.imshow('S', s)
    cv2.imshow('V', v)

    # get masks by imposing limits on the channels
    mask_h = np.logical_and( h >20, h <50) # assumming green color has hue 60 
    showMask('mask_h', mask_h)

    mask_s = np.logical_and( s >100, s <255) 
    showMask('mask_s', mask_s)

    mask_v = np.logical_and( v >60, v <255) 
    showMask('mask_v', mask_v)

    # Putting the mask alltoghether
    mask = np.logical_and(mask_h, mask_s)
    mask = np.logical_and(mask, mask_v)

    showMask('mask', mask)

    # Post processing using morphological operations 
    kernel = np.ones((5, 5), np.uint8)

    mask_uint8 = mask.astype(np.uint8)*255
    mask_dilated_uint8 = cv2.dilate(mask_uint8, kernel, iterations=0)
    mask_dilated = (mask_dilated_uint8.astype(float)/255).astype(np.bool)

    #cv2.imshow("mask_dilated", mask_dilated_uint8)
    showMask('dilated mask', mask_dilated)
    
    # to get the mask of thedog we negate the mask of the grass, 
    # assuming the image contains only dog and grass
    mask_dog = np.logical_not(mask_dilated)


    showMask('dog mask', mask_dog)


    cv2.waitKey(0)




    






if __name__ == "__main__":
    main()




