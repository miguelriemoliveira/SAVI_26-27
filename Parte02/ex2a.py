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

    # split of the color channels
    b, g, r = cv2.split(image)
    cv2.imshow('R', r)
    cv2.imshow('G', g)
    cv2.imshow('B', b)

    # get masks by imposing limits on the channels
    mask_r = np.logical_and( r >0, r <80) 
    #showMask('mask_r', mask_r)

    mask_g = np.logical_and( g >100, g <255) 
    #showMask('mask_g', mask_g)

    mask_b = np.logical_and( b >0, b <80) 
    #showMask('mask_b', mask_b)

    # Putting the mask alltoghether
    mask = np.logical_and(mask_r, mask_g)
    mask = np.logical_and(mask, mask_b)

    showMask('mask', mask)

    # Post processing using morphological operations 
    kernel = np.ones((5, 5), np.uint8)

    mask_uint8 = mask.astype(np.uint8)*255
    mask_dilated_uint8 = cv2.dilate(mask_uint8, kernel, iterations=2)
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




