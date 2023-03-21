#!/usr/bin/env python3
# Program for finding the position and bearing
# on images that contain the map and the red pointer
# Imports
import sys
import cv2
import numpy


# -------------------------------------------------------------------------------
# Functions


# Gradient of 2 points
# (y2 - y1) / (x2 - x1) Formula
def calculate_gradient(point1, point2):
    return (point2[1] - point1[1]) / (point2[0] - point1[0])


# Measuring the middle point of 2 points
def calculate_midpoint(point1, point2):
    x = (point1[0] + point2[0]) / 2
    y = (point1[1] + point2[1]) / 2
    return int(x), int(y)


# Argument has to have 3 points (Triangle points)
# Measure 3 Angles
# Check for the lowest angle
# Returns point with the lowest angle, which is the Tip point
# the rest of the points measure the (global var) midpoint
def get_points(three_points):
    global midpoint
    point1, point2, point3 = three_points[-3:]
    # NOTE: here I'm repeating the same variables several times
    # for the sake of simplicity
    # BAC / CAB POINT A
    BA = calculate_gradient(point1, point2)
    CA = calculate_gradient(point1, point3)
    radian_angle1 = numpy.arctan((CA - BA) / (1 + (CA * BA)))
    degree_angle1 = numpy.round(numpy.abs(numpy.degrees(radian_angle1)))
    # ABC / CBA POINT B
    AB = calculate_gradient(point1, point2)
    BC = calculate_gradient(point2, point3)
    radian_angle2 = numpy.arctan((BC - AB) / (1 + (BC * AB)))
    degree_angle2 = numpy.round(numpy.abs(numpy.degrees(radian_angle2)))
    # ACB / BCA POINT C
    AC = calculate_gradient(point1, point3)
    CB = calculate_gradient(point3, point2)
    radian_angle3 = numpy.arctan((CB - AC) / (1 + (CB * AC)))
    degree_angle3 = numpy.round(numpy.abs(numpy.degrees(radian_angle3)))
    lowest_angle = numpy.min([degree_angle1, degree_angle2, degree_angle3])

    if lowest_angle == degree_angle1:
        midpoint = calculate_midpoint(point2, point3)
        if midpoint:
            return point1
        else:
            print("Midpoint couldn't be found!")
            sys.exit()
    elif lowest_angle == degree_angle2:
        midpoint = calculate_midpoint(point1, point3)
        if midpoint:
            return point2
        else:
            print("Midpoint couldn't be found!")
            sys.exit()
    elif lowest_angle == degree_angle3:
        midpoint = calculate_midpoint(point1, point2)
        if midpoint:
            return point3
        else:
            print("Midpoint couldn't be found!")
            sys.exit()
    else:
        print("Midpoint or Tip point couldn't be found!")
        sys.exit()


# Calculating Bearing (clockwise angle from north)
# https://stackoverflow.com/a/64807404/17519952
def calculate_bearing(point1, point2):
    x = point2[0] - point1[0]
    y = point2[1] - point1[1]
    if x == 0:
        if y == 0:
            bearing = 0
        else:
            bearing = 0 if point1[1] > point2[1] else 180
    elif y == 0:
        bearing = 90 if point1[0] < point2[0] else 270
    else:
        bearing = numpy.arctan(y / x) / numpy.pi * 180
        lowering = point1[1] < point2[1]
        if (lowering and bearing < 0) or (not lowering and bearing > 0):
            bearing += 270
        else:
            bearing += 90
    return bearing


# Rearranges the points
# https://pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/
def rearrange(points):
    points = points.reshape((4, 2))
    rearranged_points = numpy.zeros((4, 1, 2), dtype=numpy.int32)
    add = points.sum(1)
    rearranged_points[0] = points[numpy.argmin(add)]
    rearranged_points[3] = points[numpy.argmax(add)]
    diff = numpy.diff(points, axis=1)
    rearranged_points[1] = points[numpy.argmin(diff)]
    rearranged_points[2] = points[numpy.argmax(diff)]
    return rearranged_points


# Checks for the biggest contour
def calculate_biggest_contour(contours_arg):
    biggest_contours = numpy.array([])
    maximum_area = 0
    for contour in contours_arg:
        area = cv2.contourArea(contour)
        if area > 5000:
            arc_length = cv2.arcLength(contour, True)
            approx_contours = cv2.approxPolyDP(contour, 0.02 * arc_length, True)
            if area > maximum_area and len(approx_contours) == 4:
                biggest_contours = approx_contours
                maximum_area = area
    return biggest_contours


# Main Program

if len(sys.argv) != 2:
    print("Usage: %s <image-file>" % sys.argv[0], file=sys.stderr)
    exit(1)

for fn in sys.argv[1:]:
    # Load the image
    try:
        image = cv2.imread(fn)
        # cache image height, width and channels
        height, width, channels = image.shape
        # turn image into grayscale
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # blur the grayscale image
        blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 1)
        # Canny Edge Detection
        threshold_image = cv2.Canny(blurred_image, 50, 200)
        # 5x5 identity matrix containing ones
        identity_matrix = numpy.ones((5, 5))
        # Dilation - adds pixels on object boundaries
        dilation_image = cv2.dilate(threshold_image,
                                    identity_matrix,
                                    iterations=2)
        # Erosion - removes pixels on object boundaries
        threshold_image = cv2.erode(dilation_image,
                                    identity_matrix,
                                    iterations=1)
        # Check for contours
        try:
            contours, _1 = cv2.findContours(threshold_image,
                                        cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)
            # Check for the biggest contour of the map
            biggest_contour_map = calculate_biggest_contour(contours)

            if biggest_contour_map.size != 0:
                biggest_contour_map = rearrange(biggest_contour_map)
                # Perspective transformation points
                points_array_1 = numpy.float32(biggest_contour_map)
                # corner points of original image
                points_array_2 = numpy.float32([[0, 0],
                                                [width, 0],
                                                [0, height],
                                                [width, height]])
                # Perspective transformation
                transformation = cv2.getPerspectiveTransform(points_array_1,
                                                             points_array_2)
                # Warp Perspective - (can be displayed)
                warped_image = cv2.warpPerspective(image,
                                                   transformation,
                                                   (width, height))
                # Removes 20 pixels from sides
                warped_image = warped_image[20:warped_image.shape[0] - 20,
                               20:warped_image.shape[1] - 20]
            else:
                print("Map Biggest contour not found!")
                break
            # Warped image
            bgr2hsv_image = cv2.cvtColor(warped_image, cv2.COLOR_BGR2HSV)

            # Red colour range 1
            lowest_red = numpy.array([0, 50, 50])
            highest_red = numpy.array([10, 255, 255])
            masking_0 = cv2.inRange(bgr2hsv_image, lowest_red, highest_red)

            # Red colour range 2
            lowest_red = numpy.array([170, 50, 50])
            highest_red = numpy.array([180, 255, 255])
            masking_1 = cv2.inRange(bgr2hsv_image, lowest_red, highest_red)

            # Colour masking / limiting color channels
            colour_masking = masking_0 + masking_1

            # image with the red triangle and black background only
            red_triangle_image = warped_image.copy()
            red_triangle_image[numpy.where(colour_masking == 0)] = 0

            try:
                # Check for contours
                contours, _2 = cv2.findContours(cv2.cvtColor
                                    (red_triangle_image, cv2.COLOR_BGR2GRAY),
                                    cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_NONE)
                # Check for the biggest contour of the triangle
                contours_length = [(cv2.contourArea(contour), contour)
                                   for contour
                                   in contours]
                biggest_contour = max(contours_length, key=lambda x: x[0])[1]

                # Finds a triangle of minimum area
                # enclosing the given set of 2D points
                _3, triangle = cv2.minEnclosingTriangle(biggest_contour)
                # 3 points
                triangle_points = numpy.int32(
                                    numpy.squeeze(
                                    numpy.round(triangle)))
                # Check for the tip point
                tip_point = get_points(triangle_points)

                # switching to 0 to 1 ratio
                new_x = (tip_point[0] / width)
                # switching to 0 to 1 ration and inverting
                # so the origin is from bottom-left corner
                new_y = ((height - tip_point[1]) / height)

                print("The filename to work on is %s." % sys.argv[1])
                bearing_degree = calculate_bearing(midpoint, tip_point)
                print("POSITION %.3f %.3f" % (new_x, new_y))
                print("BEARING %.1f" % bearing_degree)
            except Exception:
                print("Contours not found!", sys.exc_info())
        except Exception:
            print("Contours not found!", sys.exc_info())
    except FileNotFoundError:
        print("File not found!", sys.exc_info()[0])
# NOTE: Some lines can be further simplified
# to free up some cache, but I believe that is
# unnecessary, as it is easier to read
# Program is executed pretty quickly, so I believe
# that algorithms used are fine and might even
# be executed at a video rate

# -------------------------------------------------------------------------------
