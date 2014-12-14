import cv2
import numpy as np
from hough import hough_lines
from hough import draw_rho_theta_lines
from hough import draw_x1y1_x2y2_lines
from hough import rho_theta_to_x1y1_x2y2

# The code for this function was taken from:
# http://stackoverflow.com/questions/20677795/find-the-point-of-intersecting-lines
def line_intersection(line1, line2):
    if line1 == line2:  # Technically not true, but useful here
        return (-1, -1)
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1]) #Typo was here
    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]
    div = det(xdiff, ydiff)
    if div == 0:
        raise Exception('lines do not intersect')
    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y


# Determine whether or not two lines intersect somewhere in the image and return
# a Boolean value
def intersection_within_image(line1, line2, img_shape):
    num_rows = img_shape[0]
    num_cols = img_shape[1]
    point = line_intersection(line1, line2)
    # What about parallel lines???
    # Protip: you can chain comparison operators in Python together like
    # 1 < x < 5 instead of the more verbose 1 < x and x < 5
    if not (0 <= point[0] < num_cols and 0 <= point[1] < num_rows):
        return False
    return True


def find_squares_in_image(img):
    '''
    Find the vertices all of the four-sided polygons in the image
    '''
    # Get the hough lines for the image
    ave_lines = hough_lines(img)

    # Sanity check, we need at least four lines for the image to be used
    if len(ave_lines) < 4:
        print "ERROR - not enough lines detected in the image"
        exit(1)

    # Get the ((x1,y1),(x2,y2)) from the (rho, theta) representation
    x_y_lines = rho_theta_to_x1y1_x2y2(ave_lines, np.shape(img))

    # Split the lines into two groups, based on the fact that intersecting lines should
    # not be in the same group. We intermediately use sets to perform set subtraction.
    group1 = set([x_y_lines[0]])
    group2 = set()
    while len(group1) + len(group2) != len(x_y_lines):
        addTo1 = []
        addTo2 = []
        for line1 in group1:
            for line2 in set(x_y_lines)-group1-group2:
                if intersection_within_image(line1, line2, np.shape(img)):
                    addTo2.append(line2)
        for line2 in group2:
            for line1 in set(x_y_lines)-group1-group2:
                if intersection_within_image(line2, line1, np.shape(img)):
                    addTo1.append(line1)
        for x in addTo1:
            group1.add(x)
        for y in addTo2:
            group2.add(y)
    group1 = list(group1)
    group2 = list(group2)

    # Now find all of the four-sided polygons
    polys = []
    for i in range(len(group1)):
        for j in range(i + 1, len(group1)):
            for k in range(len(group2)):
                for l in range(k + 1, len(group2)):
                    line1 = group1[i]
                    line2 = group1[j]
                    line3 = group2[k]
                    line4 = group2[l]
                    if (intersection_within_image(line1, line3, np.shape(img))
                    and intersection_within_image(line1, line4, np.shape(img))
                    and intersection_within_image(line2, line4, np.shape(img))
                    and intersection_within_image(line2, line4, np.shape(img))):
                        p1 = line_intersection(line1, line3)
                        p2 = line_intersection(line1, line4)
                        p3 = line_intersection(line2, line3)
                        p4 = line_intersection(line2, line4)
                        polys.append((p1, p2, p3, p4))

    return polys, group1, group2


def find_smallest_square(polys):
    ''' 
    Of all the quadrangles in an image, find the coordinates of the corners
    of the smallest one, which is likely to be a square
    '''
    def distance(p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        return np.sqrt((x1-x2)**2 + (y1-y2)**2)
    dists = [distance(p1, p2)**2 + distance(p3, p4)**2 for p1,p2,p3,p4 in polys]
    p1,p2,p3,p4 = polys[dists.index(min(dists))]

    return [p1, p2, p3, p4]

def draw_corners(img, corners, color):
    ''' 
    Draw the corners of a square on an image.
    
    Parameters:
    img (array-like)
    corners (list) - must have 4 elements
    color (tuple) - must have 3 integer elements all in the range 0-255
    '''
    assert(0 <= color[0] <= 255 and 0 <= color[1] <= 255 and 0 <= color[2] <= 255)
    cv2.circle(img, corners[0], 10, color, -1)
    cv2.circle(img, corners[1], 10, color, -1)
    cv2.circle(img, corners[2], 10, color, -1)
    cv2.circle(img, corners[3], 10, color, -1)

# Run this demonstration if we're running this as a script
if __name__ == '__main__':
    # Specify the image path and get the color image
    image_path = '../data/m7/IMG_0289.JPG'
    color_img = cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
    polys, group1, group2 = find_squares_in_image(color_img)

    #just_ave_lines = draw_rho_theta_lines(ave_lines, np.zeros(np.shape(color_img)), (255, 255, 255))
    #color_img_with_lines = draw_rho_theta_lines(ave_lines, color_img, (0, 255, 0))

    # Draw the colored lines on the image
    color_img_with_lines = draw_x1y1_x2y2_lines(group1, color_img, (0, 255, 0))
    color_img_with_lines = draw_x1y1_x2y2_lines(group2, color_img_with_lines, (255, 0, 0))
    corners = find_smallest_square(polys)
    draw_corners(color_img_with_lines, corners, (255, 0, 0))
    # Draw circles on the corners of the smallest detected square


    cv2.imshow('foo', color_img_with_lines)
    cv2.waitKey()
