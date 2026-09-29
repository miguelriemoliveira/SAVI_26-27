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
    image = cv2.imread("images/person_4.jpg")
    # image = cv2.imread("images/person_3.jpg")
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
    mask_h = np.logical_and( h >20, h <60) # assumming green color has hue 60 
    showMask('mask_h', mask_h)

    mask_s = np.logical_and( s >60, s <255) 
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
    mask_dilated_uint8 = cv2.dilate(mask_uint8, kernel, iterations=2)
    mask_dilated = (mask_dilated_uint8.astype(float)/255).astype(np.bool)

    #cv2.imshow("mask_dilated", mask_dilated_uint8)
    showMask('dilated mask', mask_dilated)
    
    # to get the mask of thedog we negate the mask of the grass, 
    # assuming the image contains only dog and grass
    mask_dog = np.logical_not(mask_dilated)
    mask_dog = mask_dog.astype(np.uint8)*255 # convert numpy image to opencv format [0,1]
    cv2.imshow('dog mask', mask_dog)


    # Separate the mask into several components and find the largest one
    numLabels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_dog)
    print('numLabels = ', str(numLabels))

    # How to get the area of one component. 
    idx_component = 2
    area_2 = stats[idx_component, cv2.CC_STAT_AREA]
    print('area of component 2 = ', str(area_2))

    # Lets get the largest component by area.
    largest_area = 0
    largest_area_idx = None

    # Start searching from 1 onward because 0 is the background
    for idx_component in range(1, numLabels): # iterate all components
        area_component = stats[idx_component, cv2.CC_STAT_AREA]

        if area_component > largest_area: # found a larger one
            largest_area = area_component
            largest_area_idx = idx_component


    print('largest_area_idx = ' , str(largest_area_idx), ' with area = ' , str(largest_area))

    # Get a mask of the largest component
    largest_mask = (labels == largest_area_idx).astype(np.uint8)*255 

    cv2.imshow('largest_mask', largest_mask)

    # Get the bounding box of the largest object
    pts = cv2.findNonZero(largest_mask) # gest the row, col coords of all white pixels
    x, y, width, height = cv2.boundingRect(pts)
    print('pts:' , str(pts))
    print('x ' , str(x), 'y ' , str(y), 'w ', str(width) , 'h ', str(height))

    # Draw the found bounding box on the orignial image
    image_annototed = image.copy()
    cv2.rectangle(image_annototed, (x, y), (x+width, y+height), (255, 0, 0), 2)

    cv2.imshow('Image Annotated', image_annototed)


    ## ----------------------------------------
    ## Ex 3b
    ## ----------------------------------------

    # Compute some features of the objects we extract

    # Feature1: height_to_width_ratio
    h_w_ratio = height / width
    print('Height to width ration = ' , str(round(h_w_ratio,2)))

    # Feature2: object_area_to_image_area_ratio
    # You are compute object to object bbox area ratio
    area_image = W*H # where did I get this?
    area_object = largest_area
    area_ratio = area_object/area_image
    print('Area ratio = ', str(round(area_ratio,2)))

    # Feature3: average color of the hue component in the object
    avg_h = np.mean(h) # average of the hue component
    print('avg_h for the entire image = ', str(avg_h))

    # To get the average of only one region use masked arrays
    ma = np.ma.masked_array(h, mask=largest_mask, dtype=np.uint8)
    avg_h_object = np.mean(ma)
    print('avg_h_objet = ', str(avg_h_object))

    # THIS IS WRONG!!!!
    # CANNOT COMPUTE AND AVERAGE OF A CIRCULAR VARIABLE
    

    ## ----------------------------------------
    ## Ex 3c
    ## ----------------------------------------
    # HOW TO CLASSIFY? The idea is to decide which class is in the image.
    # Lets use the only one that maes sense, the h_w_ratio

    if h_w_ratio > 1.5:
        print('Classification result: Its a person!')
    else:
        print('Classification result: Its a dog!')


    cv2.waitKey(0)

if __name__ == "__main__":
    main()




