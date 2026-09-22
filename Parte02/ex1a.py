#!/usr/bin/env python3 
# Shebang line" specifies the interpreter. 

# imports --------------------
import cv2




# Main function
def main(): # this is our main function
    print("SAVI exercise")


    # absolute path
    image = cv2.imread("/Users/mike/Library/CloudStorage/GoogleDrive-m.riem.oliveira@gmail.com/My Drive/UA/Aulas/2026-2027/1ºSem/SAVI_26_27/SAVI_26-27/Parte02/images/dog_2.jpg")

    # relative path
    image = cv2.imread("images/dog_2.jpg")

    print("shape = " + str(image.shape))
    print("dtype = " + str(image.dtype))

    # print(image)

    cv2.imshow("Image", image)


    # Get the grayscale image
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


    print("gray shape = " + str(gray_image.shape))
    print("gray dtype = " + str(gray_image.dtype))
    cv2.imshow("Gray Image", gray_image)
    cv2.waitKey(0)


    






if __name__ == "__main__":
    main()




