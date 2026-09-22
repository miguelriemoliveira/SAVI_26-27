#!/usr/bin/env python3 
# Shebang line" specifies the interpreter. 

# imports --------------------
import cv2

# Main function
def main(): # this is our main function
    print("SAVI exercise")

    # relative path
    image = cv2.imread("images/dog_2.jpg")

    print("shape = " + str(image.shape))
    print("dtype = " + str(image.dtype))

    height, width, channels = image.shape
    image = cv2.resize(image, (round(height/3), round(width/3) ))
    #cv2.imshow("Image", image)

    # Get the grayscale image
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    print("gray shape = " + str(gray_image.shape))
    print("gray dtype = " + str(gray_image.dtype))
    cv2.imshow("Gray Image", gray_image)


    # How to get a portion of the image?
    left_side_image = gray_image[:, 0:512]
    #cv2.imshow("Left side image", left_side_image)

    dog_tail = gray_image[1:round(895/2), 512:1024]
    #cv2.imshow("Dog Tail", dog_tail)

    # resize an image
    resize_image = cv2.resize(gray_image, (256, 512))
    #cv2.imshow("Resized Image", resize_image)

    # brighten the image
    bright_image = gray_image + 20
    cv2.imshow("Bright Image", bright_image)



    cv2.waitKey(0)


    






if __name__ == "__main__":
    main()




