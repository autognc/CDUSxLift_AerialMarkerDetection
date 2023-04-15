import cv2 as cv
import math
import numpy as np
import metrics2D as est
import decodeConst as dcdc
import drawingTools as dt

def determineCandidateRectIDbars( src_atleast_grys, debug_mode ):
        img_height, img_width = src_atleast_grys.shape
        rect_contours, rect_contours_pass1, rect_contour_centroids, rect_contour_angles, rect_contour_areas, poly_contour_areas = [], [], [], [], [], []
        canny_output = cv.Canny( src_atleast_grys, 10, 200, True )
        contours, _ = cv.findContours( canny_output, cv.RETR_TREE, cv.CHAIN_APPROX_TC89_KCOS )
        for ii in range(0,len(contours)):
                approx_cp = cv.approxPolyDP( contours[ii], 0.025*cv.arcLength(contours[ii],True), True )
                approx_cp_area = abs( cv.contourArea(approx_cp) )
                rect_contours_pass1.append( contours[ii] )
                if( (     approx_cp_area > img_height * img_width * pow(float(dcdc.RECT_AREA_PERCENT_THRESHOLD)/100,2) ) \
                      and len(approx_cp) >= dcdc.RECT_IDENTIFIER_SIDES_LOWER_THRESHOLD \
                      and len(approx_cp) <= dcdc.RECT_IDENTIFIER_SIDES_UPPER_THRESHOLD  ):
                        approx_rect_center, approx_rect_size, approx_rect_angle  = cv.minAreaRect(approx_cp)
                        approx_aspectr = max( approx_rect_size[0]/approx_rect_size[1], approx_rect_size[1]/approx_rect_size[0] )

                        if(    approx_aspectr > (1 - float(dcdc.RECT_ASPECT_RATIO_LOWER_PERECNT_ERROR_THRESHOLD)/100) * dcdc.MEASURED_ASPECT_RATIO 
                           and approx_aspectr < (1 + float(dcdc.RECT_ASPECT_RATIO_UPPER_PERECNT_ERROR_THRESHOLD)/100) * dcdc.MEASURED_ASPECT_RATIO ):
                                rect_contour_areas.append( approx_rect_size[0]*approx_rect_size[1] )
                                poly_contour_areas.append( approx_cp_area ) # NOT THE SAME AS THE ONE ABOVE
                                rect_contours.append( contours[ii] )
                                rect_contour_centroids.append(approx_rect_center)
                                if( approx_rect_size[0] < approx_rect_size[1] ):
                                        rect_contour_angles.append(approx_rect_angle)
                                else:
                                        rect_contour_angles.append( 90. - approx_rect_angle )
        
        if(debug_mode):
                dt.showContours(contours,"CONTOURS IN D3",src_atleast_grys.shape)
                cv.waitKey(0)

        return rect_contours, rect_contours_pass1, rect_contour_centroids, rect_contour_angles, rect_contour_areas, poly_contour_areas



def determineWarpedImageFrom4IdBars(image, rect_contour_centroids, debug_mode):
        fc_relative_angles = []
        quadrant0_flag = False
        quadrant3_flag = False
        for ii in range(1,4):
                anglei = est.angleBetweenPoints(rect_contour_centroids[0],rect_contour_centroids[ii])
                if( est.determineAngleQuadrant(anglei) == 0 ):
                        quadrant0_flag = True
                elif( est.determineAngleQuadrant(anglei) == 3 ):
                        quadrant3_flag = True
                fc_relative_angles.append(anglei)
        
        if( quadrant0_flag and quadrant3_flag ):
                for ii in range(0,3):
                        anglei = fc_relative_angles[ii] + math.pi; 
                        if( anglei > 2*math.pi ):
                                anglei = anglei - 2*math.pi
                        fc_relative_angles[ii] = anglei

        fc_ra_max = fc_relative_angles[0]
        fc_ra_min = fc_ra_max
        fc_ra_max_indx = int(1)
        fc_ra_min_indx = int(1)

        for ii in range(2,4):
                anglei = fc_relative_angles[ii-1]
                if( anglei < fc_ra_min ):
                        fc_ra_min = anglei
                        fc_ra_min_indx = ii
                elif( anglei > fc_ra_max ): 
                        fc_ra_max = anglei
                        fc_ra_max_indx = ii

        fc_median_indx = int(0)
        for ii in range(2,4):
            if( ii != fc_ra_min_indx and ii != fc_ra_max_indx ):
                fc_median_indx = ii
        
        fc_median_distance =  est.euclideanDistance( rect_contour_centroids[0],rect_contour_centroids[fc_median_indx])

        ordered_centroids = np.array( [ [ rect_contour_centroids[0], rect_contour_centroids[fc_ra_min_indx], \
                                          rect_contour_centroids[fc_median_indx], rect_contour_centroids[fc_ra_max_indx] ] ] , \
                                      dtype = "float32" )
        
        perspective_transformed_centroids = np.array( [ [ ( 0.0, 0.5*fc_median_distance), ( 0.5*fc_median_distance, 0.0), \
                                                          ( fc_median_distance, 0.5*fc_median_distance), ( 0.5*fc_median_distance, fc_median_distance) ] ], \
                                                          dtype = "float32" )
        
        transformationMat = cv.getPerspectiveTransform(ordered_centroids, perspective_transformed_centroids)
        warped_image = cv.warpPerspective(image, transformationMat, (int(fc_median_distance), int(fc_median_distance)))
        
        return warped_image,fc_median_distance



def determineWarpedImageFrom2or3IdBars(image, rect_contour_centroids, rect_contour_angles, DEBUG_MODE):
        # TODO: DETERMINE THE ROATION ANGLE IS INCONSITENT (OFF BY 180 IN CERTAIN UNIDENTIFIED CONDITIONS)
        ref_angle = rect_contour_angles[0]
        slope = math.tan ( ref_angle * math.pi / 180.0 )
        yinter = rect_contour_centroids[0][1] - slope*rect_contour_centroids[0][0]
        above_reference_line = ( rect_contour_centroids[1][1] - (slope*rect_contour_centroids[1][0] + yinter) ) > 0

        fc_median_distance = 0.
        if( abs(ref_angle - rect_contour_angles[0]) > 45.0 ):
                fc_median_distance = 2 * est.euclideanDistance( rect_contour_centroids[0],rect_contour_centroids[1]) / math.sqrt(2)
        else:
                fc_median_distance = est.euclideanDistance( rect_contour_centroids[0],rect_contour_centroids[1])
        
        delta_angle = 0

        # TODO: TEST THIS DELTA ANGLE DETERMINATION
        if(above_reference_line):
                delta_angle = 90 - ref_angle
        else:
                delta_angle = -90 - ref_angle

        img_height, img_width,_ = image.shape
        rotatedimageSize = ( int(2*img_height) , int(2*img_width)  )

        transformationMat = cv.getRotationMatrix2D( rect_contour_centroids[0], delta_angle, 1 )
        rotatedImage = cv.warpAffine(image, transformationMat, rotatedimageSize )
        warped_image = rotatedImage[ int(rect_contour_centroids[0][1]-0.5*fc_median_distance):int( rect_contour_centroids[0][1]+0.5*fc_median_distance ) , \
                                     int(rect_contour_centroids[0][0]):int(rect_contour_centroids[0][0]+fc_median_distance ) ]
        
        return warped_image, fc_median_distance



def attemptIdBarCorrections( rect_contours , rect_contour_centroids, rect_contour_angles , rect_contour_areas , poly_contour_areas, debug_mode, image_shape ):
        # 1ST PROTECTION FOR MORE THAN 4 BARS (CENTROID PROXIMITY) -START
        rect_contours_corr, rect_contour_centroids_corr, rect_contour_angles_corr, rect_contour_areas_corr, poly_contour_areas_corr = [], [], [], [], []
        rect_contours_corr.append( rect_contours[0] )
        rect_contour_centroids_corr.append( rect_contour_centroids[0] )
        rect_contour_angles_corr.append( rect_contour_angles[0] )
        rect_contour_areas_corr.append( rect_contour_areas[0] )
        poly_contour_areas_corr.append( poly_contour_areas[0] )

        for ii in range( 1, len(rect_contour_centroids) ):
                pass_flag = True
                
                for jj in range( 0, len(rect_contour_centroids_corr) ):
                        if( est.euclideanDistance( rect_contour_centroids[ii], rect_contour_centroids_corr[jj] ) <= float(dcdc.CONTOUR_ED_THRES) ):
                                # DO A SIZE CHECK TO CHOOSE WHICH TO REPLACE 
                                pass_flag = False 
                                break
                
                if( pass_flag ):
                        rect_contours_corr.append( rect_contours[ii] )
                        rect_contour_centroids_corr.append( rect_contour_centroids[ii] )
                        rect_contour_angles_corr.append( rect_contour_angles[ii] )
                        rect_contour_areas_corr.append( rect_contour_areas[ii]  )
                        poly_contour_areas_corr.append( poly_contour_areas[ii] )

        
        rect_contours = rect_contours_corr
        rect_contour_centroids = rect_contour_centroids_corr
        rect_contour_angles = rect_contour_angles_corr
        rect_contour_areas = rect_contour_areas_corr
        poly_contour_areas = poly_contour_areas_corr
        if(debug_mode):
                        dt.showContours(rect_contours,"CONTOURS AFTER FIRST PROTECTION",image_shape)
                        cv.waitKey(0)
        # 1ST PROTECTION FOR MORE THAN 4 BARS (CENTROID PROXIMITY) - END


        # 2ND PROTECTION FOR MORE THAN 4 BARS ( RECT APPROX STD METHOD ) - START
        if( len(rect_contour_centroids) > 1 ):

                rect_contours_corr, rect_contour_centroids_corr, rect_contour_angles_corr, rect_contour_areas_corr, poly_contour_areas_corr = [], [], [], [], []
                for ii in range( 0, len(rect_contour_areas) ):
                        pass_flag = True
                        for jj in range( 0, len(rect_contour_areas) ):
                                relative_size_perc = rect_contour_areas[ii]/rect_contour_areas[jj]
                                if( relative_size_perc < (dcdc.REL_RECT_SIZE_PERCENT_THRESH/100) ):
                                        pass_flag = False
                                        break

                        if pass_flag:
                                rect_contours_corr.append( rect_contours[ii] )
                                rect_contour_centroids_corr.append( rect_contour_centroids[ii] )
                                rect_contour_angles_corr.append( rect_contour_angles[ii] )
                                rect_contour_areas_corr.append( rect_contour_areas[ii]  )
                                poly_contour_areas_corr.append( poly_contour_areas[ii] )
                
                rect_contours = rect_contours_corr
                rect_contour_centroids = rect_contour_centroids_corr
                rect_contour_angles = rect_contour_angles_corr
                rect_contour_areas = rect_contour_areas_corr
                poly_contour_areas = poly_contour_areas_corr

                # CUTOFF IF TOO MANY 
                if( len(rect_contour_areas) > dcdc.RECT_CUTOFF_SIZE ):
                        sorted_indx = np.argsort(  np.array( rect_contour_areas ) )
                        # TRIM THE NUMBER OF CONTOURS BASED ON AREA
                        rect_contours = [ rect_contours[sorted_indx[ii]] for ii in range(0,dcdc.RECT_CUTOFF_SIZE) ]
                        rect_contour_centroids = [ rect_contour_centroids[sorted_indx[ii]] for ii in range(0,dcdc.RECT_CUTOFF_SIZE) ]
                        rect_contour_angles = [ rect_contour_angles[sorted_indx[ii]] for ii in range(0,dcdc.RECT_CUTOFF_SIZE) ]
                        rect_contour_areas = [ rect_contour_areas[sorted_indx[ii]] for ii in range(0,dcdc.RECT_CUTOFF_SIZE) ]
                        poly_contour_areas = [ poly_contour_areas[sorted_indx[ii]] for ii in range(0,dcdc.RECT_CUTOFF_SIZE) ]

                if(debug_mode):
                        dt.showContours(rect_contours,"CONTOURS AFTER TRIMMING",image_shape)
                        cv.waitKey(0)

                size_before = len(rect_contour_areas)
                while( len(rect_contour_areas) > 4 ):
                        rect_contours_corr, rect_contour_centroids_corr, rect_contour_angles_corr, rect_contour_areas_corr, poly_contour_areas_corr = [], [], [], [], []
                        rect_contour_areas_mean = sum(  rect_contour_areas )/len(rect_contour_areas)
                        var = sum(  [ pow( recti_area - rect_contour_areas_mean, 2 ) for recti_area in rect_contour_areas]  ) / len(rect_contour_areas)
                        std = pow( var, 0.5 )
                        for ii in range( 0, len(rect_contour_centroids) ):
                                if(  abs(rect_contour_areas_mean-rect_contour_areas[ii]) <= std ):
                                        rect_contours_corr.append( rect_contours[ii] )
                                        rect_contour_centroids_corr.append( rect_contour_centroids[ii] )
                                        rect_contour_angles_corr.append( rect_contour_angles[ii] )
                                        rect_contour_areas_corr.append( rect_contour_areas[ii]  )
                                        poly_contour_areas_corr.append( poly_contour_areas[ii] )

                        rect_contours = rect_contours_corr
                        rect_contour_centroids = rect_contour_centroids_corr
                        rect_contour_angles = rect_contour_angles_corr
                        rect_contour_areas = rect_contour_areas_corr
                        poly_contour_areas = poly_contour_areas_corr

                        if( len(rect_contour_areas) ) == size_before:
                                break 
                        else:
                                size_before = len(rect_contour_areas) 

                if(debug_mode):
                        dt.showContours(rect_contours,"CONTOURS AFTER SECOND PROTECTION",image_shape)
                        cv.waitKey(0)
        # 2ND PROTECTION FOR MORE THAN 4 BARS ( RECT APPROX STD METHOD ) - END


        # # 3RD PROTECTION FOR MORE THAN 4 BARS ( CONTOUR TRUE STD METHOD ) - START
        # if( len(rect_contour_centroids) > 1 ):
        #         rect_contours_corr = []
        #         rect_contour_centroids_corr = []
        #         rect_contour_angles_corr = []
        #         rect_contour_areas_corr = []
        #         poly_contour_areas_corr = []
                
        #         # CUTOFF IF TOO MANY 
        #         if( len(rect_contour_areas) > dcdc.RECT_CUTOFF_SIZE ):
        #                 sorted_indx = np.argsort(  np.array( rect_contour_areas_corr ) )
        #                 # TRIM THE NUMBER OF CONTOURS BASED ON AREA
        #                 rect_contours = [ rect_contours[sorted_indx[ii]] for ii in range(0,dcdc.RECT_CUTOFF_SIZE) ]
        #                 rect_contour_centroids = [ rect_contour_centroids[sorted_indx[ii]] for ii in range(0,dcdc.RECT_CUTOFF_SIZE) ]
        #                 rect_contour_angles = [ rect_contour_angles[sorted_indx[ii]] for ii in range(0,dcdc.RECT_CUTOFF_SIZE) ]
        #                 rect_contour_areas = [ rect_contour_areas[sorted_indx[ii]] for ii in range(0,dcdc.RECT_CUTOFF_SIZE) ]
        #                 poly_contour_areas = [ poly_contour_areas[sorted_indx[ii]] for ii in range(0,dcdc.RECT_CUTOFF_SIZE) ]


        #         poly_contour_areas_mean = sum(  poly_contour_areas )/len(poly_contour_areas)
        #         var = sum(  [ pow( polyi_area - poly_contour_areas_mean, 2 ) for polyi_area in poly_contour_areas]  ) / len(poly_contour_areas)
        #         std = pow( var, 0.5 )
        #         for ii in range( 0, len(rect_contour_centroids) ):
        #                 if(  abs(poly_contour_areas_mean-poly_contour_areas[ii]) <= std ):
        #                         rect_contours_corr.append( rect_contours[ii] )
        #                         rect_contour_centroids_corr.append( rect_contour_centroids[ii] )
        #                         rect_contour_angles_corr.append( rect_contour_angles[ii] )
        #                         rect_contour_areas_corr.append( rect_contour_areas[ii]  )
        #                         poly_contour_areas_corr.append( poly_contour_areas[ii] )

        #         rect_contours = rect_contours_corr
        #         rect_contour_centroids = rect_contour_centroids_corr
        #         rect_contour_angles = rect_contour_angles_corr
        #         rect_contour_areas = rect_contour_areas_corr
        #         poly_contour_areas = poly_contour_areas_corr
        #         if(debug_mode):
        #                 dt.showContours(rect_contours,"CONTOURS AFTER THIRD PROTECTION",image_shape)
        #                 cv.waitKey(0)
        # # 3RD PROTECTION FOR MORE THAN 4 BARS ( CONTOUR TRUE STD METHOD ) - END

        return rect_contours , rect_contour_centroids, rect_contour_angles , rect_contour_areas , poly_contour_areas



def determineCIDIndices( src_eval_contours, row_seg, col_seg, segment_area, debug_mode ):
        # LOCATING CIRCULAR IDENTIFIER - START
        cid_corner_indx = int(-1)
        cid_indx = int(-1) 
        crnr0_img, crnr1_img, crnr2_img, crnr3_img = [], [], [], []
        crnr0_cntrs, crnr1_cntrs, crnr2_cntrs, crnr3_cntrs  = [], [], [], []
        crnr0_total_area, crnr1_total_area, crnr2_total_area, crnr3_total_area = 0.0, 0.0, 0.0, 0.0
        crnr0_area_nonzero, crnr1_area_nonzero, crnr2_area_nonzero, crnr3_area_nonzero  = False, False, False, False 

        for ii in range(0,dcdc.ENCODING_LENGTH,2):
                for jj in range(0,dcdc.ENCODING_LENGTH,2):
                        indx = ii*dcdc.ENCODING_LENGTH + jj
                        cid_eval_SegementSubmatrix = src_eval_contours[ ii*row_seg:(ii+1)*row_seg-1 , jj*col_seg:(jj+1)*col_seg-1 ]
                        if( indx == 0 ):
                                crnr0_img = cid_eval_SegementSubmatrix
                        elif( indx == 2 ):
                                crnr1_img = cid_eval_SegementSubmatrix
                        elif( indx == 6 ):
                                crnr2_img = cid_eval_SegementSubmatrix
                        elif( indx == 8 ):
                                crnr3_img = cid_eval_SegementSubmatrix

                        canny_output = cv.Canny( cid_eval_SegementSubmatrix, 10, 200 )
                        contours, _ = cv.findContours( canny_output, cv.RETR_TREE, cv.CHAIN_APPROX_TC89_L1 )
                        for kk in range(0,len(contours)):
                                approx_cp = cv.approxPolyDP( contours[kk], 0.01*cv.arcLength(contours[kk],True), True )
                                if( len(approx_cp) > dcdc.CIRC_IDENTIFIER_SIDES_THRESHOLD  ):
                                        approx_min_circ_center,approx_min_circ_radius = cv.minEnclosingCircle( contours[kk] )
                                        approx_cp_area = math.pi * pow(approx_min_circ_radius,2)
                                        if(    approx_cp_area < ( segment_area ) * (dcdc.SEGMENT_LCIRC_RATIO) * (1 + float(dcdc.CIRC_AREA_UPPER_PERCENT_THRESHOLD)/100) \
                                           and approx_cp_area > ( segment_area ) * (dcdc.SEGMENT_SCIRC_RATIO) * (1 - float(dcdc.CIRC_AREA_LOWER_PERCENT_THRESHOLD)/100)  ):
                                                if( indx == 0 ):
                                                        crnr0_cntrs.append( contours[kk] )
                                                        crnr0_total_area = crnr0_total_area + approx_cp_area
                                                        if( not crnr0_area_nonzero):
                                                                crnr0_area_nonzero = True
                                                elif( indx == 2 ):
                                                        crnr1_cntrs.append( contours[kk] )
                                                        crnr1_total_area = crnr1_total_area + approx_cp_area
                                                        if( not crnr1_area_nonzero):
                                                                crnr1_area_nonzero = True
                                                elif( indx == 6 ):
                                                        crnr2_cntrs.append( contours[kk] )
                                                        crnr2_total_area = crnr2_total_area + approx_cp_area
                                                        if( not crnr2_area_nonzero):
                                                                crnr2_area_nonzero = True
                                                elif( indx == 8 ):
                                                        crnr3_cntrs.append( contours[kk] )
                                                        crnr3_total_area = crnr3_total_area + approx_cp_area
                                                        if( not crnr3_area_nonzero):
                                                                crnr3_area_nonzero = True


        if( debug_mode ):
                print( "[DEBUG] CIRC-ID IS IN " + str(cid_indx) + "R-POSITION" )
                
                crnr0_show_img = crnr0_img
                crnr1_show_img = crnr1_img
                crnr2_show_img = crnr2_img
                crnr3_show_img = crnr3_img

                cv.imshow("THRESHED IMAGE OF ENCODING", src_eval_contours)
                dt.showContoursOnImage(crnr0_cntrs,"CORNER0 CONTOURS IN D1",crnr0_show_img)
                dt.showContoursOnImage(crnr1_cntrs,"CORNER1 CONTOURS IN D1",crnr1_show_img)
                dt.showContoursOnImage(crnr2_cntrs,"CORNER2 CONTOURS IN D1",crnr2_show_img)
                dt.showContoursOnImage(crnr3_cntrs,"CORNER3 CONTOURS IN D1",crnr3_show_img)
                cv.waitKey(0)

        if(dcdc.DECODER_SHOWCASE_MODE):
                show_image = src_eval_contours
                for ii in range(0,dcdc.ENCODING_LENGTH,2):
                        for jj in range(0,dcdc.ENCODING_LENGTH,2):
                                indx = ii*dcdc.ENCODING_LENGTH + jj
                                drawingSegementSubmatrix = show_image[ ii*row_seg:(ii+1)*row_seg-1 , jj*col_seg:(jj+1)*col_seg-1 ]
                                if( indx == 0 ):
                                        show_image[ ii*row_seg:(ii+1)*row_seg-1 , jj*col_seg:(jj+1)*col_seg-1 ] = \
                                                dt.drawContoursOnImage( crnr0_cntrs , drawingSegementSubmatrix )
                                elif( indx == 2 ):
                                        show_image[ ii*row_seg:(ii+1)*row_seg-1 , jj*col_seg:(jj+1)*col_seg-1 ] = \
                                                dt.drawContoursOnImage( crnr1_cntrs , drawingSegementSubmatrix )
                                elif( indx == 6 ):
                                        show_image[ ii*row_seg:(ii+1)*row_seg-1 , jj*col_seg:(jj+1)*col_seg-1 ] = \
                                                dt.drawContoursOnImage( crnr2_cntrs , drawingSegementSubmatrix )
                                elif( indx == 8 ):
                                        show_image[ ii*row_seg:(ii+1)*row_seg-1 , jj*col_seg:(jj+1)*col_seg-1 ] = \
                                                dt.drawContoursOnImage( crnr3_cntrs , drawingSegementSubmatrix )
                cv.imshow("PASSING CIRCULAR CONTOURS IN D1 AND THEIR CENTROIDS",show_image)
                cv.waitKey(0)

        if( not( crnr0_area_nonzero or crnr1_area_nonzero or crnr2_area_nonzero or crnr3_area_nonzero ) ):
                return cid_corner_indx, cid_indx, False
        
        cid_corner_indx = np.array( [ crnr0_total_area, crnr1_total_area, crnr2_total_area, crnr3_total_area ] ).argmax()        
        if( cid_corner_indx == 0 ):
                cid_indx = int(0)
        elif( cid_corner_indx == 1 ):
                cid_indx = int(2)
        elif( cid_corner_indx == 2 ):
                cid_indx = int(6)
        elif( cid_corner_indx == 3 ):
                cid_indx = int(8)

        return cid_corner_indx, cid_indx, True
        # LOCATING CIRCULAR IDENTIFIER - END



def evaluateV2BitEncoding( src_atleast_grys, row_seg, col_seg, segment_area, cid_indx, cid_corner_indx, debug_mode ):
        decode_image = src_atleast_grys
        decode_blur = cv.medianBlur( decode_image, 3 )

        pre_bit_pass = True
        pre_bit_encoding = []
        segment_percentw_vec = []
        row_sub_seg = int(row_seg/2)
        col_sub_seg = int(col_seg/2)
        indx0_img, indx1_img, indx2_img, indx3_img, indx4_img, indx5_img, indx6_img, indx7_img, indx8_img  = [], [], [], [], [], [], [], [], []

        for ii in range(0,dcdc.ENCODING_LENGTH):
                for jj in range(0,dcdc.ENCODING_LENGTH):

                        indx = ii*dcdc.ENCODING_LENGTH + jj

                        if( indx == cid_indx): 
                                pre_bit_encoding.append(-1) 
                                continue

                        segmentSubMatrix = decode_blur[ ii*row_seg:(ii+1)*row_seg-1, jj*col_seg:(jj+1)*col_seg-1 ]
                        _,sSM_thresh_bin = cv.threshold( segmentSubMatrix.astype(np.uint8), 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU )

                        if( indx == 0 ):
                                indx0_img = sSM_thresh_bin
                        elif( indx == 1 ):
                                indx1_img = sSM_thresh_bin
                        elif( indx == 2 ):
                                indx2_img = sSM_thresh_bin
                        elif( indx == 3 ):
                                indx3_img = sSM_thresh_bin
                        elif( indx == 4 ):
                                indx4_img = sSM_thresh_bin
                        elif( indx == 5 ):
                                indx5_img = sSM_thresh_bin
                        elif( indx == 6 ):
                                indx6_img = sSM_thresh_bin
                        elif( indx == 7 ):
                                indx7_img = sSM_thresh_bin
                        elif( indx == 8 ):
                                indx8_img = sSM_thresh_bin

                        sSM_thresh_bin = sSM_thresh_bin/255

                        segment_percentw = 0.0
                        for kk in range(0,2):
                                for ll in range(0,2):
                                        if( kk*2 + ll != cid_corner_indx):
                                                segmentSubSubMatrix = sSM_thresh_bin[ kk*row_sub_seg:(kk+1)*row_sub_seg-1, ll*col_sub_seg:(ll+1)*col_sub_seg-1 ]
                                                segment_percentw = segment_percentw + cv.sumElems(segmentSubSubMatrix)[0]/(0.75*segment_area)
                        
                        segment_percentw_vec.append(segment_percentw)

                        if( abs(segment_percentw - 0.5) > dcdc.DECODING_CONFIDENCE_THRESHOLD - 0.5  ):
                                if( (segment_percentw - 0.5) < 0 ):
                                        pre_bit_encoding.append(0)
                                else:
                                        pre_bit_encoding.append(1)
                        else:
                                pre_bit_encoding.append(-2)
                                pre_bit_pass = False


        if(debug_mode):
                show_image = src_atleast_grys
                for ii in range(0,dcdc.ENCODING_LENGTH):
                        for jj in range(0,dcdc.ENCODING_LENGTH):
                                indx = ii*dcdc.ENCODING_LENGTH + jj
                                if( indx == cid_indx): 
                                        continue
                                elif( indx == 0 ):
                                        show_image[ ii*row_seg:(ii+1)*row_seg-1 , jj*col_seg:(jj+1)*col_seg-1 ] = indx0_img
                                elif( indx == 1 ):
                                        show_image[ ii*row_seg:(ii+1)*row_seg-1 , jj*col_seg:(jj+1)*col_seg-1 ] = indx1_img
                                elif( indx == 2 ):
                                        show_image[ ii*row_seg:(ii+1)*row_seg-1 , jj*col_seg:(jj+1)*col_seg-1 ] = indx2_img
                                elif( indx == 3 ):
                                        show_image[ ii*row_seg:(ii+1)*row_seg-1 , jj*col_seg:(jj+1)*col_seg-1 ] = indx3_img
                                elif( indx == 4 ):
                                        show_image[ ii*row_seg:(ii+1)*row_seg-1 , jj*col_seg:(jj+1)*col_seg-1 ] = indx4_img
                                elif( indx == 5 ):
                                        show_image[ ii*row_seg:(ii+1)*row_seg-1 , jj*col_seg:(jj+1)*col_seg-1 ] = indx5_img
                                elif( indx == 6 ):
                                        show_image[ ii*row_seg:(ii+1)*row_seg-1 , jj*col_seg:(jj+1)*col_seg-1 ] = indx6_img
                                elif( indx == 7 ):
                                        show_image[ ii*row_seg:(ii+1)*row_seg-1 , jj*col_seg:(jj+1)*col_seg-1 ] = indx7_img
                                elif( indx == 8 ):
                                        show_image[ ii*row_seg:(ii+1)*row_seg-1 , jj*col_seg:(jj+1)*col_seg-1 ] = indx8_img

                cv.imshow("BINARIZED D1 SEGMENTS",show_image)
                cv.waitKey(0)


        if( not pre_bit_pass ):
                decode_image = src_atleast_grys
                pre_bit_pass = True
                pre_bit_encoding = []
                segment_percentw_vec = []
                _,decode_image_tzthresh = cv.threshold( 255-decode_image, 255-dcdc.DECODING_GREYSCALE_THRESH, 255, cv.THRESH_TOZERO)
                decode_image_tzthresh = 255 - decode_image_tzthresh
                decode_blur = cv.medianBlur( decode_image_tzthresh, 3 )
                for ii in range(0,dcdc.ENCODING_LENGTH):
                        for jj in range(0,dcdc.ENCODING_LENGTH):
                                if( ii*dcdc.ENCODING_LENGTH + jj == cid_indx): 
                                        pre_bit_encoding.append(-1) 
                                        continue
                                segmentSubMatrix = decode_blur[ ii*row_seg:(ii+1)*row_seg-1, jj*col_seg:(jj+1)*col_seg-1 ]/255
                                _,sSM_thresh_bin = cv.threshold( segmentSubMatrix.astype(np.uint8), 0, 255, cv.THRESH_BINARY + cv.THRESH_TRIANGLE )
                                sSM_thresh_bin = sSM_thresh_bin/255

                                segment_percentw = 0.0
                                for kk in range(0,2):
                                        for ll in range(0,2):
                                                if( kk*2 + ll != cid_corner_indx):
                                                        segmentSubSubMatrix = sSM_thresh_bin[ kk*row_sub_seg:(kk+1)*row_sub_seg-1, ll*col_sub_seg:(ll+1)*col_sub_seg-1 ]
                                                        segment_percentw = segment_percentw + cv.sumElems(segmentSubSubMatrix)[0]/(0.75*segment_area)
                                
                                segment_percentw_vec.append(segment_percentw)

                                if( abs(segment_percentw - 0.5) > dcdc.DECODING_CONFIDENCE_THRESHOLD - 0.5  ):
                                        if( (segment_percentw - 0.5) < 0 ):
                                                pre_bit_encoding.append(0)
                                        else:
                                                pre_bit_encoding.append(1)
                                else:
                                        pre_bit_encoding.append(-2)
                                        pre_bit_pass = False
        
        return pre_bit_encoding, pre_bit_pass



def evaluateV1BitEncoding( src_atleast_grys, row_seg, col_seg, segment_area, cid_indx, debug_mode ):
        decode_image = src_atleast_grys
        decode_blur = cv.medianBlur( decode_image, 3 )
        _,decode_thresh_bin = cv.threshold( decode_blur, 0, 255, cv.THRESH_BINARY + cv.THRESH_TRIANGLE )
        
        pre_bit_pass = True
        pre_bit_encoding = []
        segment_percentw_vec = []
        for ii in range(0,dcdc.ENCODING_LENGTH):
                for jj in range(0,dcdc.ENCODING_LENGTH):
                        if( ii*dcdc.ENCODING_LENGTH + jj == cid_indx): 
                                pre_bit_encoding.append(-1) 
                                continue
                        segmentSubMatrix = decode_thresh_bin[ ii*row_seg:(ii+1)*row_seg-1, jj*col_seg:(jj+1)*col_seg-1 ]/255
                        segment_percentw = cv.sumElems(segmentSubMatrix)[0]/segment_area
                        segment_percentw_vec.append(segment_percentw)

                        if( abs(segment_percentw - 0.5) > dcdc.DECODING_CONFIDENCE_THRESHOLD - 0.5  ):
                                if( (segment_percentw - 0.5) < 0 ):
                                        pre_bit_encoding.append(0)
                                else:
                                        pre_bit_encoding.append(1)
                        else:
                                pre_bit_encoding.append(-2)
                                pre_bit_pass = False


        if( not pre_bit_pass ):
                decode_image = src_atleast_grys
                pre_bit_pass = True
                pre_bit_encoding = []
                segment_percentw_vec = []
                _,decode_image_tzthresh = cv.threshold( 255-decode_image, 255-dcdc.DECODING_GREYSCALE_THRESH, 255, cv.THRESH_TOZERO)
                decode_image_tzthresh = 255 - decode_image_tzthresh
                decode_blur = cv.medianBlur( decode_image_tzthresh, 3 )
                _,decode_thresh_bin = cv.threshold( decode_blur, 0, 255, cv.THRESH_BINARY + cv.THRESH_TRIANGLE )
                for ii in range(0,dcdc.ENCODING_LENGTH):
                        for jj in range(0,dcdc.ENCODING_LENGTH):
                                if( ii*dcdc.ENCODING_LENGTH + jj == cid_indx): 
                                        pre_bit_encoding.append(-1) 
                                        continue
                                segmentSubMatrix = decode_thresh_bin[ ii*row_seg:(ii+1)*row_seg-1, jj*col_seg:(jj+1)*col_seg-1 ]/255
                                segment_percentw = cv.sumElems(segmentSubMatrix)[0]/segment_area
                                segment_percentw_vec.append(segment_percentw)

                                if( abs(segment_percentw - 0.5) > dcdc.DECODING_CONFIDENCE_THRESHOLD - 0.5  ):
                                        if( (segment_percentw - 0.5) < 0 ):
                                                pre_bit_encoding.append(0)
                                        else:
                                                pre_bit_encoding.append(1)
                                else:
                                        pre_bit_encoding.append(-2)
                                        pre_bit_pass = False
        
        return pre_bit_encoding, pre_bit_pass



def readMappedEncoding( cid_indx, pre_bit_encoding ):
        # APPARENTLY SWITCH/MATCH STATEMENTS ARE NEW TO PYTHON
        if( cid_indx == 0 ):
                bit_encoding = [ int(pre_bit_encoding[1]),int(pre_bit_encoding[2]),int(pre_bit_encoding[3]),int(pre_bit_encoding[4]), \
                                        int(pre_bit_encoding[5]),int(pre_bit_encoding[6]),int(pre_bit_encoding[7]),int(pre_bit_encoding[8]) ]
        elif( cid_indx == 2 ):
                bit_encoding = [ int(pre_bit_encoding[5]),int(pre_bit_encoding[8]),int(pre_bit_encoding[1]),int(pre_bit_encoding[4]), \
                                        int(pre_bit_encoding[7]),int(pre_bit_encoding[0]),int(pre_bit_encoding[3]),int(pre_bit_encoding[6]) ]
        elif( cid_indx == 6 ):
                bit_encoding = [ int(pre_bit_encoding[3]),int(pre_bit_encoding[0]),int(pre_bit_encoding[7]),int(pre_bit_encoding[4]), \
                                        int(pre_bit_encoding[1]),int(pre_bit_encoding[8]),int(pre_bit_encoding[5]),int(pre_bit_encoding[2]) ]
        elif( cid_indx == 8 ):
                bit_encoding = [ int(pre_bit_encoding[7]),int(pre_bit_encoding[6]),int(pre_bit_encoding[5]),int(pre_bit_encoding[4]), \
                                        int(pre_bit_encoding[3]),int(pre_bit_encoding[2]),int(pre_bit_encoding[1]),int(pre_bit_encoding[0]) ]
        
        return bit_encoding