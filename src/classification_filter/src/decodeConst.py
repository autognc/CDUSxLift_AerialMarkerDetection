import numpy as np

ENCODING_VERSION = 2

#// DEBUG PROPERTIES
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
DECODER_SHOWCASE_MODE = False
DECODER_DEBUG_MODE = 3
#  0 - NONE
#  1 - DEBUGGER MODE FOR D1 EXTRACTION
#  2 - DEBUGGER MODE FOR ENCODING DETERMINATION
#  3 - DEBUGGER MODE FOR BOTH MODES (1)(2)

DECODER_ON_HARDWARE = True
DECODER_VERBOSE_MODE = False
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



#/// MEASURED PROPERTIES 
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#// // FOR COMPUTER GENERATED IMAGES
# ENCODING_LENGTH 3
# MEASURED_ASPECT_RATIO 9.615
# ENCODING_CROP_RATIO 0.1772151899
# SEGMENT_LCIRC_RATIO 0.7853981634
# dcdc.SEGMENT_SCIRC_RATIO 0.0872664626

#// // FOR IRL IMAGES
ENCODING_LENGTH = 3
MEASURED_ASPECT_RATIO = 6.0
ENCODING_CROP_RATIO = 0.1666666667
SEGMENT_LCIRC_RATIO = 0.7853981634
SEGMENT_SCIRC_RATIO = 0.0872664626
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



#/// TUNING PARAMETERS
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
GREYSCALE_TO_255_THRESHOLD = 255

RECT_AREA_PERCENT_THRESHOLD = 0.15
RECT_ASPECT_RATIO_LOWER_PERECNT_ERROR_THRESHOLD = 25
RECT_ASPECT_RATIO_UPPER_PERECNT_ERROR_THRESHOLD = 25

RECT_PERIM_LOWER_PERECNT_ERROR_THRESHOLD = 20
RECT_PERIM_UPPER_PERECNT_ERROR_THRESHOLD = 20

RECT_IDENTIFIER_SIDES_LOWER_THRESHOLD = 4
RECT_IDENTIFIER_SIDES_UPPER_THRESHOLD = 8

REL_RECT_SIZE_PERCENT_THRESH = 10

RECT_CUTOFF_SIZE = 7

CONTOUR_EDIST_PERCENT_THRES = 7.5
 
RECT_MINIMUM_SCREEN_PERCENTAGE = .1
RECT_BOUNDING_CONTOUR_AREA_THRESHOLD = 30
RECT_UPPER_COMPARISON_PERCENT_ERROR_THRESHOLD = 30
RECT_LOWER_COMPARISON_PERCENT_ERROR_THRESHOLD = 30

RECT_PARALLEL_ANGLE_THRESH = 30
RECT_CENTROID_DISTANCE_THRESHOLD = 20

RECT_INSIDE_DISTANCE_THRESHOLD = 20

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
CIRC_AREA_LOWER_PERCENT_THRESHOLD = 30
CIRC_AREA_UPPER_PERCENT_THRESHOLD = 10
CIRC_IDENTIFIER_SIDES_THRESHOLD = 10

DECODING_ENC_CONFIDENCE_THRESHOLD = 0.65
DECODING_ID_CONFIDENCE_THRESHOLD = 0.55
# DECODING_GREYSCALE_THRESH = 150
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



#// MORPHING PROPERTIES
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
GRADIENT_MORPH_SIZE = 1
CLOSING_MORPH_SIZE = 0
MEDIAN_BLUR_SIZE = 1
GAUSS_BLUR_MORPH_SIZE = 2
DILATION_MORPH_SIZE = 1
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


#//POSE CONSTANTS - CURRENTLY ANTONIOS LAPTOP CAMERA
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
CAMERA_MATRIX = np.array([[ 608.54554687,  0,            306.08689476],\
                          [0,              610.79113343, 249.15590665],\
                          [0,              0,            1]],dtype = "float32")
DISTANCE_COEFFICIENTS = np.array([-0.06171222,  
                                0.31699824,
                                0.00144633,
                                -0.00316355,
                                -0.69987865], dtype = "float32")