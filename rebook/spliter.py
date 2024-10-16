import cv2
import numpy as np

def book_spliter(image, segment, f_points):
    """
    Splits the given image of a book into left and right pages based on segment.

    Parameters:
    ----------
    image : np.ndarray
        The input image of the book, where splitting needs to be performed.
    segment : YOLO output
        The segmentation data used to find the split area of the book.
    f_points : np.ndarray, np.array([[100, 200], [150, 250], ...])
        Feature points that provide finger markers.

    Returns:
    -------
    book_left : np.ndarray
        Rotated left page of the book image.
    book_right : np.ndarray
        Rotated right page of the book image.
    ctr_l : tuple
        The optical center coordinate for the left page.
    ctr_r : tuple
        The optical center coordinate for the right page.
    f_points_l : np.ndarray
        Landmarks of the left hand.
    f_points_r : np.ndarray
        Landmarks of the right hand.
    """
    max_area = 0
    largest_contour = None
    img_mask_shrinked = None
    for r in segment:
        img = np.copy(r.orig_img)

        for ci, c in enumerate(r):
            label = c.names[c.boxes.cls.tolist().pop()]
            if label != 'book': continue
            contour = c.masks.xy.pop().astype(np.int32).reshape(-1, 1, 2)
            area = cv2.contourArea(contour)
            if area > max_area:
                max_area = area
                largest_contour = contour
        
        if largest_contour is not None:
            mask_orignal = np.zeros(img.shape[:2], np.uint8)
            cv2.drawContours(mask_orignal, [largest_contour], -1, (255, 255, 255), cv2.FILLED)
            cv2.drawContours(mask_orignal, [largest_contour], -1, (0, 0, 0), thickness=50)
            
            contour_shrinked, center_point = shrink_contour(largest_contour, scale=0.7)
            
            mask_shrinked = cv2.drawContours(np.zeros(img.shape[:2], np.uint8), [contour_shrinked], -1, (255, 255, 255), cv2.FILLED)
            
            img_mask_shrinked = img.copy()
            img_mask_shrinked[mask_shrinked == 0] = (255, 255, 255)
    
    if img_mask_shrinked is None:
        return None
    gray = cv2.cvtColor(img_mask_shrinked, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    x, y, w, h = cv2.boundingRect(cv2.bitwise_not(binary))

    length_diagonal = (w**2 + h**2)**0.5 / 2
    x0 = int(x + w/2 - length_diagonal)
    y0 = int(y + h/2 - length_diagonal)
    w = int(2*length_diagonal)
    h = int(2*length_diagonal)
    if x0 >=0 and y0 >=0 and (x0+w) <= binary.shape[1] and (y0+h) <=binary.shape[0]:
        binary_squarified = binary[y0:y0+h, x0:x0+w]
    else:
        binary_squarified = np.full((h, w), 255, dtype=binary.dtype)
        valid_area = (max(x0,0), min(x0+w,binary.shape[1]), max(y0,0), min(y0+h,binary.shape[0]))
        binary_squarified[valid_area[2]-y0:valid_area[3]-y0,valid_area[0]-x0:valid_area[1]-x0] = \
            binary[max(y0,0):min(y0+h,binary.shape[0]), max(x0,0):min(x0+w,binary.shape[1])]

    x_c = image.shape[1]/2 - x0
    y_c = image.shape[0]/2 - y0

    b_contours, _ = cv2.findContours(cv2.bitwise_not(binary_squarified), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_height = 0
    max_contour = None
    angle = None

    for contour in b_contours:
        rect = cv2.boundingRect(contour)
        xmin, ymin, width, height = rect
        if height > max_height:
            max_height = height
            max_contour = contour

    if max_contour is None:
        return None
    max_contour = cv2.convexHull(max_contour)

    xmin, ymin, width, height = cv2.boundingRect(max_contour)
    area = cv2.contourArea(max_contour)

    if area / height < 30 and height > binary_squarified.shape[0] / 3:
        min_y_point = tuple(max_contour[max_contour[:, :, 1].argmin()][0])
        max_y_point = tuple(max_contour[max_contour[:, :, 1].argmax()][0])

        x_min, y_min = min_y_point
        x_max, y_max = max_y_point
        x_min += x0
        x_max += x0
        y_min += y0
        y_max += y0

        ratio = (y_max - y_min) / (x_max - x_min)
        angle = np.degrees(np.arctan(ratio))
        if angle >= 0:
            angle = 90 - angle
        else:
            angle = -90 - angle
        
        x7 = int(x_min - y_min/ratio)
        y7 = 0
        x8 = int(x_min - (y_min - image.shape[0])/ratio)
        y8 = image.shape[0]

    if angle is None:
        size_smaller = min(500, binary_squarified.shape[0])
        ratio = size_smaller / binary_squarified.shape[0]
        binary_resized = cv2.resize(binary_squarified, (size_smaller, size_smaller))

        binary_inv = cv2.bitwise_not(binary_resized)
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(binary_inv, kernel, iterations=1)
        dilated_inv = cv2.bitwise_not(dilated)

        max_num = 0
        max_len = 0
        index = 0
        for i in range(-45, 45, 1):
            rotated_image = rotate_image(dilated_inv, i)

            colsums = np.sum(rotated_image, axis=0)
            for idx, col in enumerate(colsums):
                if col != rotated_image.shape[0]*255:
                    first_idx = idx
                    break
            for idx, col in enumerate(reversed(colsums)):
                if col != rotated_image.shape[0]*255:
                    last_idx = len(colsums) - 1 - idx
                    break
            
            index_shift = (last_idx - first_idx) // 20
            sliced_colsums = colsums[first_idx+index_shift:last_idx-index_shift + 1]

            sum = np.max(sliced_colsums)
            max_index = np.where(sliced_colsums == sum)[0] + first_idx + index_shift

            if sum >= max_num and len(max_index) > max_len:
                max_num = sum
                max_len = len(max_index)
                angle = i
                index = max_index[len(max_index) // 2]
                
        index = int(index / ratio + x0)

        shift_pixel = 0
        xx, yy = rotate_point(index-shift_pixel, 0, center_point, -angle)
        k0 = np.tan((angle+90)*np.pi/180)
        y7 = 0
        y8 = image.shape[0]
        x7 = xx - yy/k0
        x8 = xx - (yy - y8)/k0
        angle = -angle

    book_left, x_c_l, y_c_l, f_points_l = split_lr(image, mask_orignal, [x7, y7, x8, y8], angle, 'LEFT', f_points)
    book_right, x_c_r, y_c_r, f_points_r = split_lr(image, mask_orignal, [x7, y7, x8, y8], angle, 'RIGHT', f_points)

    ctr_l = np.array((x_c_l, y_c_l))
    ctr_r = np.array((x_c_r, y_c_r))

    # cv2.imwrite('book_left.png', book_left)
    # cv2.imwrite('book_right.png', book_right)

    return book_left, book_right, ctr_l, ctr_r, f_points_l, f_points_r
    
def rotate_image(image, angle, center=None, scale=1.0, bg=(255, 255, 255)):
    (h, w) = image.shape[:2]
    if center is None:
        center = (w // 2, h // 2)

    M = cv2.getRotationMatrix2D(center, angle, scale)
    rotated = cv2.warpAffine(image, M, (w, h), borderValue=bg)
    
    return rotated

def rotate_point(x, y, center, angle_deg):
    cx, cy = center
    angle_rad = np.deg2rad(angle_deg)
    x_shifted = x - cx
    y_shifted = y - cy
    x_rotated = x_shifted * np.cos(angle_rad) + y_shifted * np.sin(angle_rad)
    y_rotated = -x_shifted * np.sin(angle_rad) + y_shifted * np.cos(angle_rad)
    x_final = x_rotated + cx
    y_final = y_rotated + cy
    
    return int(x_final), int(y_final)

def shrink_contour(contour, scale=0.8):
    M = cv2.moments(contour)
    if M['m00'] == 0:
        return contour
    cx = int(M['m10'] / M['m00'])
    cy = int(M['m01'] / M['m00'])
    
    shrink_contour = []
    for point in contour:
        x, y = point[0]
        new_x = cx + scale * (x - cx)
        new_y = cy + scale * (y - cy)
        shrink_contour.append([[int(new_x), int(new_y)]])
    
    return np.array(shrink_contour, dtype=np.int32), (cx, cy)

def safe_rotate(image, angle):
    im_h, im_w = image.shape[:2]
    angle_rad = np.deg2rad(angle)

    im_h_new = im_w * abs(np.sin(angle_rad)) + im_h * abs(np.cos(angle_rad))
    im_w_new = im_h * abs(np.sin(angle_rad)) + im_w * abs(np.cos(angle_rad))

    pad_h = int(np.ceil((im_h_new - im_h) / 2))
    pad_w = int(np.ceil((im_w_new - im_w) / 2))
    pads = ((pad_h, pad_h), (pad_w, pad_w)) + ((0, 0),) * (len(image.shape) - 2)

    padded = np.pad(image, pads, 'constant', constant_values=0)
    padded_h, padded_w = padded.shape[:2]
    matrix = cv2.getRotationMatrix2D((padded_w / 2, padded_h / 2), angle, 1)
    result = cv2.warpAffine(padded, matrix, (padded_w, padded_h),
                            borderMode=cv2.BORDER_CONSTANT,
                            borderValue=0)
    
    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    colsums = np.sum(binary, axis=0)
    for idx, col in enumerate(colsums):
        if col != 0:
            first_col = idx
            break
    for idx, col in enumerate(reversed(colsums)):
        if col != 0:
            last_col = len(colsums) - 1 - idx
            break

    rowsums = np.sum(binary, axis=1)
    for idx, col in enumerate(rowsums):
        if col != 0:
            first_row = idx
            break
    for idx, col in enumerate(reversed(rowsums)):
        if col != 0:
            last_row = len(rowsums) - 1 - idx
            break

    pad = 5
    first_col = max(first_col-pad, 0)
    last_col  = min(last_col+pad, padded_w)
    first_row = max(first_row-pad, 0)
    last_row  = min(last_row+pad, padded_h)

    return result[first_row:last_row,first_col:last_col], padded_w/2-first_col, padded_h/2-first_row

def split_lr(image, mask, split_points, angle, lr, f_points):
    x1, y1, x2, y2 = split_points
    cropped = image.copy()
    d_mask = mask.copy()
    h, w, _ = cropped.shape

    if lr == 'LEFT':
        s_points = np.array([[x1, y1], [image.shape[1], 0], [image.shape[1], image.shape[0]], [x2, y2]], dtype=np.int32)
    elif lr == 'RIGHT':
        s_points = np.array([[0, 0], [x1, y1], [x2, y2], [0, image.shape[0]]], dtype=np.int32)
    cv2.fillPoly(d_mask, [s_points], color=(0, 0, 0))

    cropped[d_mask == 0] = (0, 0, 0)

    x, y, w, h = cv2.boundingRect(d_mask)
    cropped = cropped[y:y+h, x:x+w]
    x_c = image.shape[1]/2 - (x + w/2)
    y_c = image.shape[0]/2 - (y + h/2)

    rotated, x_0, y_0 = safe_rotate(cropped, -angle)
    x_c, y_c = rotate_point(x_c, y_c, (0, 0), -angle)
    x_c += x_0
    y_c += y_0
    
    rotated_f_points = []
    if f_points:
        for p in f_points:
            p_x, p_y = rotate_point(p[0] - (x + w/2), p[1] - (y + h/2), (0, 0), -angle)
            p_x += x_0
            p_y += y_0
            rotated_f_points.append([p_x, p_y])
        if lr == 'LEFT': 
            rotated_f_points = [p for p in rotated_f_points if p[0] <= rotated.shape[1] / 2]
            rotated_f_points = sorted(rotated_f_points, key=lambda x: x[1])
        elif lr == 'RIGHT':
            rotated_f_points = [p for p in rotated_f_points if p[0] >= rotated.shape[1] / 2]
            rotated_f_points = sorted(rotated_f_points, key=lambda x: x[1])

    return rotated, x_c, y_c, rotated_f_points

def find_f_points(image, page_lr):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) > 0:
        contour = max(contours, key=cv2.contourArea)
        
        min_x = np.min(contour[:, 0, 0])
        threshold_x = min_x + (np.max(contour[:, 0, 0]) - min_x) * 0.5
        if page_lr == "LEFT":
            cropped_contour = np.array([pt for pt in contour if pt[0][0] < threshold_x])
        elif page_lr =="RIGHT":
            cropped_contour = np.array([pt for pt in contour if pt[0][0] > threshold_x])

        if len(cropped_contour) > 3:
            convexHull = cv2.convexHull(cropped_contour, returnPoints=False)
            defects = cv2.convexityDefects(cropped_contour, convexHull)
            if defects is not None:
                max_dist = 0
                point_max_dist = None
                for i in range(defects.shape[0]):
                    s, e, f, d = defects[i, 0]
                    start = tuple(cropped_contour[s][0])
                    end = tuple(cropped_contour[e][0])
                    far = tuple(cropped_contour[f][0])
                    if d > max_dist:
                        max_dist = d
                        point_max_dist = cropped_contour[f][0]

                return point_max_dist

    return None