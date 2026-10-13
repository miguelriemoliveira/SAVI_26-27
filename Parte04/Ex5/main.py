#!/usr/bin/env python3 
# Shebang line" specifies the interpreter. 

# imports --------------------
import argparse
from random import randint
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

def showScaledImage(window_name, image, scale):

    # scale image then show
    resized_image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL) # test other options to see if the image window resizes . Does not work on mac!
    cv2.imshow(window_name, resized_image)

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
    ap.add_argument("-is", "--image_scale", type=float, required=False, 
                    default=1.0, help="Scale of images to display", )
    ap.add_argument("-dlr", "--david_lowes_ratio", type=float, required=False, 
                    default=0.5, help="David Lowe's ratio for the ratio test", )
    ap.add_argument("-nk", "--number_of_keypoints", type=int, required=False, 
                    default=500, help="Number of keypoints", )
    ap.add_argument("-ip", "--image_pair", type=str, required=False, 
                    default="santorini", help="Parent folder that will contain the two images 1 and 2.png", )


    args = ap.parse_args()
    args = vars(args) # transform the args into a dictionary
    print('Input args: ' + str(args))

    # Load the images
    train_image = cv2.imread('../images/' + args['image_pair'] + '/1.png')
    query_image = cv2.imread('../images/' + args['image_pair'] + '/2.png')

    # create the gui images for displaying
    train_image_gui = train_image.copy()
    query_image_gui = query_image.copy()


    # Compute features using sift
    sift_detector = cv2.SIFT_create(nfeatures=args['number_of_keypoints'])
    t_key_points, t_descriptors = sift_detector.detectAndCompute(train_image, None)
    q_key_points, q_descriptors = sift_detector.detectAndCompute(query_image, None)

    # print('t_key_points'  + str(t_key_points))

    # Match of keypoints
    index_params = dict(algorithm=1, trees = 15)
    search_params = dict(checks= 50)
    flann_matcher = cv2.FlannBasedMatcher(index_params, search_params)

    # Do the actual matching
    # k is the number of matches to return (to be changed later)
    # Now we want to get not only the best matche, but also the second best match
    two_best_matches = flann_matcher.knnMatch(q_descriptors, t_descriptors, k=2)

    matches = []
    for best_match_idx, two_best_match_tuple in enumerate(two_best_matches):

        best_match = two_best_match_tuple[0] # best match is the first in the tuple
        second_best_match = two_best_match_tuple[1] # best match is the second in the tuple


        # Using David Lowe's ratio test we discard matches in which the best and second best are very close
        if best_match.distance < args['david_lowes_ratio'] * second_best_match.distance:
            matches.append(best_match) # Add the match to the list
        else:
            continue # so we do not draw the circles in the train and query images

        # Get tehe train and query indexes of the match
        t_idx = best_match.trainIdx
        q_idx = best_match.queryIdx

        # Get the coordinates of the keypoins of that match
        t_x, t_y = int(t_key_points[t_idx].pt[0]), int(t_key_points[t_idx].pt[1])
        q_x, q_y = int(q_key_points[q_idx].pt[0]), int(q_key_points[q_idx].pt[1])

        color = randint(0,255), randint(0,255), randint(0,255)
        cv2.circle(train_image_gui, (t_x,t_y), 55, color, 2)
        cv2.circle(query_image_gui, (q_x,q_y), 55, color, 2)


    # use an opencv function to draw the matches
    matches_images = cv2.drawMatches(query_image_gui, q_key_points, train_image_gui, t_key_points, matches, None)


    # Compute the transformation ---------------------------------------------


    # first we need to create special matrices (numpy arrays ) that opencv's findhomography requires
    # Must create a numpy array of size (n,1,2) to describe the keypoints from query and train images
    n = len(matches)
    t_key_points_nparray = np.ndarray((n,1,2), dtype=np.float32 )
    q_key_points_nparray = np.ndarray((n,1,2), dtype=np.float32 )


    # Now we travel the matches list and fill out these arrays
    for match_idx, match in enumerate(matches):

        t_idx = match.trainIdx
        q_idx = match.queryIdx

        # Get the x,y of the keypoint in the train and query images
        t_x, t_y = t_key_points[t_idx].pt[0], t_key_points[t_idx].pt[1]
        q_x, q_y = q_key_points[q_idx].pt[0], q_key_points[q_idx].pt[1]

        # Add the x,y values to the arrays
        t_key_points_nparray[match_idx, 0, 0] = t_x
        t_key_points_nparray[match_idx, 0, 1] = t_y

        q_key_points_nparray[match_idx, 0, 0] = q_x
        q_key_points_nparray[match_idx, 0, 1] = q_y

    H, _ = cv2.findHomography(q_key_points_nparray, t_key_points_nparray, cv2.RANSAC)

    print('H=\n\n\n' + str(H)+ '\n\n\n')

    # Apply transformation H to the query image to get it transformed into the same coordinate system as the train image


    # Because in the case of Machu pichu the query image is contained inside the train image, the output_width and output_height are 
    # the size of the train image
    output_width = train_image.shape[1]
    output_height = train_image.shape[0]

    query_image_transformed = cv2.warpPerspective(query_image, H, (output_width, output_height))


    train_image_float = train_image.astype(float)
    query_image_transformed_float = query_image_transformed.astype(float)
    w = 0.5

    # ---------------------------------------------------------------------
    # Merge the train image and the query_image_transformed
    # Approach 1: Naive fusion. the iamge gets darker
    # ---------------------------------------------------------------------


    # mosaic_float = weight * train_image_float + (1 - weight ) * query_image_transformed_float 

    # mosaic = mosaic_float.astype(np.uint8)

    # ---------------------------------------------------------------------
    # Approach Diniz 
    # ---------------------------------------------------------------------
    # Find a way to see  waht are the valid pixels (region) in the query_iamge_transformed
    # Merge train + query_fusion_transformed only in that valud region. 
    # In the other regions (where query image _transformed is invalid), use the pixels values of the train image 

    query_image_transformed_gray = cv2.cvtColor(query_image_transformed, cv2.COLOR_RGB2GRAY)

    mask_valid_bool = np.logical_not(query_image_transformed_gray == 0)
    mask_valid = mask_valid_bool.astype(np.uint8)*255

    # we start by creating a copy of the train image which guarantees thatll the pixels in the invalid 
    # (and valid) regiosn are the same as the train 

    mosaic_float = train_image_float.copy()
    mosaic_float[mask_valid_bool] =  w * train_image_float[mask_valid_bool] + (1-w) * query_image_transformed_float[mask_valid_bool]
    mosaic = mosaic_float.astype(np.uint8)


    # lets create an aggreagate image which puts on the left the valid region of the trains image, and on the right the valie image of the 
    # query_iamge_transformed
    # valid_train_image = train_image[mask_valid_bool]
    # valid_query_image_transformed = query_image_transformed[mask_valid_bool]

    # print('valid_train_iamge.shape' + str(valid_train_image.shape))

    # showScaledImage('valid train', valid_train_image, args['image_scale'])
    # showScaledImage('valid query', valid_query_image_transformed, args['image_scale'])


    # -------------------------------------------------------------------------
    # Visualization
    # -------------------------------------------------------------------------

    # Draw keypoints on the images
    # for key_point in t_key_points:
    #     x, y = int(key_point.pt[0]), int(key_point.pt[1])
    #     color = randint(0,255), randint(0,255), randint(0,255)
    #     cv2.circle(train_image_gui, (x,y), 55, color, 2)

    # for key_point in q_key_points:
    #     x, y = int(key_point.pt[0]), int(key_point.pt[1])
    #     color = randint(0,255), randint(0,255), randint(0,255)
    #     cv2.circle(query_image_gui,(x,y), 55, color, 2)



    showScaledImage('Train', train_image_gui, args['image_scale'])
    showScaledImage('Query Transformed', query_image_transformed, args['image_scale'])
    # showScaledImage('Query', query_image_gui, args['image_scale'])
    # showScaledImage('Matches', matches_images, args['image_scale'])
    showScaledImage('Mask valid', mask_valid, args['image_scale'])
    showScaledImage('Mosaic', mosaic, args['image_scale'])



    


    cv2.waitKey(0)


if __name__ == "__main__":
    main()




