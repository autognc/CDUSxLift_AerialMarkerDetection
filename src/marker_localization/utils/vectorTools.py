import math
import numpy as np
from . import cameraConst as cmc

# NORMALIZE VECTORS
def normalized_vec3( vec ):
    norm = math.sqrt( (vec**2).sum() )
    if norm != 0:
        return vec/norm
    return np.zeros( [3,1] )


# CALCULATE CAMERA RAY UNIT VECTOR
def getCameraRayUV_C( image_pt ):
    x_p = image_pt[0]
    y_p = image_pt[1]
    
    # ARBITRARY SCALING OF THE VIEW VECTOR
    x_c_scaled, y_c_scaled, z_c_scaled = None, None, None

    if cmc.CAMERA_MODEL == 0:
        x_c_scaled = (x_p + 0.5) - cmc.IRSCAM_IMAGE_PWIDTH/2 
        y_c_scaled = cmc.IRSCAM_IMAGE_PHEIGHT/2 - (y_p + 0.5)
        z_c_scaled = cmc.IRSCAM_Z_C_SCALED
    else:
        x_c_scaled = (x_p + 0.5) - cmc.HSCAM_IMAGE_PWIDTH/2 
        y_c_scaled = cmc.HSCAM_IMAGE_PHEIGHT/2 - (y_p + 0.5)
        z_c_scaled = cmc.HSCAM_Z_C_SCALED

    return normalized_vec3( np.array( [ [x_c_scaled],[y_c_scaled],[z_c_scaled] ] ) )