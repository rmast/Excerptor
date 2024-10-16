from __future__ import division, print_function

import cv2
import math
import numpy as np
from scipy import interpolate
from skimage.measure import ransac
from numpy.polynomial import Polynomial as Poly
from . import lib
from .geometry import Line
from .lib import debug_imwrite, is_bw
from .letters import Letter, TextLine

cross33 = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))

def skew_angle(im, orig, AH, lines):
    if len(orig.shape) == 2:
        debug = cv2.cvtColor(orig, cv2.COLOR_GRAY2RGB)
    else:
        debug = orig.copy()

    alphas = []
    for l in lines:
        if len(l) < 8: continue

        line_model = l.fit_line()
        line_model.draw(debug)
        alphas.append(line_model.angle())

    debug_imwrite('lines.png', debug)

    return np.median(alphas)

def lu_dewarp(im):
    # morphological operators
    morph_a = [
        np.array([1] + [0] * (2 * i), dtype=np.uint8).reshape(2 * i + 1, 1) \
        for i in range(9)
    ]
    morph_d = [a.T for a in morph_a]
    morph_c = [
        np.array([0] * (2 * i) + [1], dtype=np.uint8).reshape(2 * i + 1, 1) \
        for i in range(9)
    ]
    # morph_b = [c.T for c in morph_c]

    im_inv = im ^ 255
    bdyt = np.zeros(im.shape, dtype=np.uint8) - 1
    for struct in morph_c + morph_d:  # ++ morph_b
        bdyt &= cv2.erode(im_inv, struct)

    debug_imwrite("bdyt.png", bdyt)
    return bdyt

    for struct in morph_c + morph_d:
        bdyt &= im_inv ^ cv2.erode(im_inv, struct)

def top_contours(contours, hierarchy):
    i = 0
    result = []
    while i >= 0:
        result.append(contours[i])
        i = hierarchy[i][0]

    return result

def all_letters(im):
    max_label, labels, stats, centroids = \
        cv2.connectedComponentsWithStats(im ^ 255, connectivity=4)
    return [Letter(label, labels, stats[label], centroids[label]) \
            for label in range(1, max_label)]

def dominant_char_height(im, letters=None):
    if letters is None:
        letters = all_letters(im)

    heights = [letter.h for letter in letters if letter.w > 10]

    hist, _ = np.histogram(heights, 256, [0, 256])
    # TODO: make depend on DPI.
    AH = np.argmax(hist[8:]) + 8  # minimum height 8

    if lib.debug:
        debug = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
        for letter in letters:
            letter.box(debug, color=lib.GREEN if letter.h == AH else lib.RED)
        debug_imwrite('heights.png', debug)

    return AH

def word_contours(AH, im):
    opened = cv2.morphologyEx(im ^ 255, cv2.MORPH_OPEN, cross33)
    horiz = cv2.getStructuringElement(cv2.MORPH_RECT, (int(AH * 0.6) | 1, 1))
    rls = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, horiz)
    debug_imwrite('rls.png', rls)

    _, contours, [hierarchy] = cv2.findContours(rls, cv2.RETR_CCOMP,
                                                cv2.CHAIN_APPROX_SIMPLE)
    words = top_contours(contours, hierarchy)
    word_boxes = [tuple([word] + list(cv2.boundingRect(word))) for word in words]
    # Slightly tuned from paper (h < 3 * AH and h < AH / 4)
    word_boxes = [__x_y_w_h for __x_y_w_h in word_boxes if __x_y_w_h[4] < 3 * AH and __x_y_w_h[4] > AH / 3 and __x_y_w_h[3] > AH / 3]

    return word_boxes

def valid_letter(AH, l):
    #TODO: optimaze for novel
    # return l.h < 6 * AH and l.w < 6 * AH and l.h > AH / 3 and l.w > AH / 4
    return l.h < 3 * AH and l.w < 3 * AH and l.h > AH / 3 and l.w > AH / 4 and l.h/l.w > 0.4 and l.h/l.w < 2.5

def filter_size(AH, im, letters=None):
    if letters is None:
        letters = all_letters(im)

    if lib.debug:
        debug = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
        for l in letters:
            l.box(debug, color=lib.GREEN if valid_letter(AH, l) else lib.RED)
        lib.debug_imwrite('size_filter.png', debug)

    # Slightly tuned from paper (h < 3 * AH and h < AH / 4)
    return [l for l in letters if valid_letter(AH, l)]

def horizontal_lines(AH, im, components=None):
    if components is None:
        components = all_letters(im)

    result = []
    for component in components:
        if component.w > AH * 10:
            mask = component.raster()
            proj = mask.sum(axis=0)
            smooth = (proj[:-2] + proj[1:-1] + proj[2:]) / 3.0
            max_height_var = np.percentile(smooth, 98) - np.percentile(smooth, 2)
            if np.percentile(smooth, 98) <= AH / 3.0 and max_height_var <= AH / 6.0:
                result.append(component)

    return result

def combine_underlined(AH, im, lines, components):
    lines_set = set(lines)
    underlines = horizontal_lines(AH, im, components)
    for underline in underlines:
        raster = underline.raster()
        bottom = underline.y + underline.h - 1 - raster[::-1].argmax(axis=0)
        close_lines = []
        for line in lines:
            base_points = line.base_points().astype(int)
            base_points = base_points[(base_points[:, 0] >= underline.x) \
                                      & (base_points[:, 0] < underline.right())]
            if len(base_points) == 0: continue

            base_ys = base_points[:, 1]
            underline_ys = bottom[base_points[:, 0] - underline.x]
            if np.all(np.abs(base_ys - underline_ys) < AH):
                line.underlines.append(underline)
                close_lines.append(line)

        if len(close_lines) > 1:
            # print('merging some underlined lines!')
            combined = close_lines[0]
            lines_set.discard(combined)
            for line in close_lines[1:]:
                lines_set.discard(line)
                combined.merge(line)

            lines_set.add(combined)

    return list(lines_set)

def hand_drawn_lines(AH, im, lines, components=None):
    if components is None:
        components = all_letters(im)

    underlines = []
    for component in components:
        if component.w > AH * 3 and component.h < AH * 4:
            mask = component.raster()
            proj = mask.sum(axis=0)
            smooth = (proj[:-2] + proj[1:-1] + proj[2:]) / 3.0
            if np.percentile(smooth, 85) <= AH / 1.0 and \
                np.percentile(smooth, 85) - np.percentile(smooth, 15) <= AH / 2.0:
                top_contour = component.top_contour()
                clipped_top_contour = top_contour.copy()
                clipped_top_contour[top_contour < np.percentile(top_contour, 20)] = np.percentile(top_contour, 20)
                for idx, line in enumerate(lines):
                    base_points = line.base_points().astype(int)
                    points_filter = (base_points[:, 0] >= component.left()) & (base_points[:, 0] < component.right())
                    base_points = base_points[points_filter]
                    if len(base_points) == 0: continue
                    base_y = base_points[:, 1]
                    y_diff = clipped_top_contour[base_points[:, 0] - component.left()] - base_y
                    if np.all((y_diff >= 0) & (y_diff < AH * 1.5)):
                        underlines.append([
                            idx, 
                            np.where(points_filter)[0][0], 
                            np.where(points_filter)[0][-1], 
                            component.left_mid(),
                            component.right_mid(),
                            ])

    if len(underlines):
        underlines = sorted(underlines, key=lambda x: (x[0], x[3][0]))
        merged_underlines = []
        for underline in underlines:
            idx, _, end_idx, left_mid, right_mid = underline
            if merged_underlines and merged_underlines[-1][0] == idx:
                _, _, _, _, last_right_mid = merged_underlines[-1]
                if abs(left_mid[0] - last_right_mid[0]) < AH * 1.5:
                    merged_underlines[-1][2] = end_idx
                    merged_underlines[-1][4] = right_mid
                    continue
            merged_underlines.append(underline)
        underlines = merged_underlines

    return underlines

def collate_lines(AH, word_boxes):
    word_boxes = sorted(word_boxes, key=lambda c_x_y_w_h: c_x_y_w_h.x)
    lines = []
    for word_box in word_boxes:
        x1, y1, w1, h1 = word_box
        # print "word:", x1, y1, w1, h1
        candidates = []
        for l in lines:
            x0, y0, w0, h0 = l[-1]
            x0p, y0p, w0p, h0p = l[-2] if len(l) > 1 else l[-1]
            if x1 < x0 + w0 + 4 * AH and y0 <= y1 + h1 and y1 <= y0 + h0:
                candidates.append((x1 - x0 - w0 + abs(y1 - y0), l))
            elif x1 < x0p + w0p + AH and y0p <= y1 + h1 and y1 <= y0p + h0p:
                candidates.append((x1 - x0p - w0p + abs(y1 - y0p), l))

        if candidates:
            candidates.sort(key=lambda d_l: d_l[0])
            _, line = candidates[0]
            line.append(word_box)
            # print "  selected:", x, y, w, h
        else:
            lines.append([word_box])

    return [TextLine(l) for l in lines]

def collate_lines_2(AH, word_boxes):
    word_boxes = sorted(word_boxes, key=lambda c_x_y_w_h1: c_x_y_w_h1.x)
    lines = []
    for word_box in word_boxes:
        x1, y1, w1, h1 = word_box
        # print "word:", x1, y1, w1, h1
        best_candidate = None
        best_score = 100000
        for l in lines:
            x0, y0, w0, h0 = l[-1]
            x0p, y0p, w0p, h0p = l[-2] if len(l) > 1 else l[-1]
            score = best_score
            if x1 < x0 + w0 + 4 * AH and y0 <= y1 + h1 and y1 <= y0 + h0:
                score = x1 - x0 - w0 + abs(y1 - y0)
            elif x1 < x0p + w0p + AH and y0p <= y1 + h1 and y1 <= y0p + h0p:
                score = x1 - x0p - w0p + abs(y1 - y0p)
            if score < best_score:
                best_score = score
                best_candidate = l

        if best_candidate:
            best_candidate.append(word_box)
            # print "  selected:", x, y, w, h
        else:
            lines.append([word_box])

    return [TextLine(l) for l in lines]

def dewarp_text(im):
    # Goal-Oriented Rectification (Stamatopoulos et al. 2011)
    im_h, im_w = im.shape

    AH = dominant_char_height(im)
    print('AH =', AH)

    word_boxes = word_contours(im)
    lines = collate_lines(AH, word_boxes)

    word_coords = [np.array([(x, y, x + w, y + h) for c, x, y, w, h in l]) for l in lines]
    bounds = np.array([
        word_coords[np.argmin(word_coords[:, 0]), 0],
        word_coords[np.argmin(word_coords[:, 2]), 2]
    ])
    line_coords = [(
        min((x for _, x, y, w, h in l)),
        min((y for _, x, y, w, h in l)),
        max((x + w for _, x, y, w, h in l)),
        max((y + h for _, x, y, w, h in l)),
    ) for l in lines]

    widths = np.array([x2_ - x1_ for x1_, y1_, x2_, y2_ in line_coords])
    median_width = np.median(widths)

    line_coords = [x1_y1_x2_y2 for x1_y1_x2_y2 in line_coords if x1_y1_x2_y2[2] - x1_y1_x2_y2[0] > median_width * 0.8]

    debug = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    for _, x, y, w, h in word_boxes:
        cv2.rectangle(debug, (x, y), (x + w, y + h), (0, 255, 0), 1)
    for x1, y1, x2, y2 in line_coords:
        cv2.rectangle(debug, (x1, y1), (x2, y2), (255, 0, 0), 2)
    debug_imwrite('lines.png', debug)

    left = np.array([(x, y) for _, x, y, _, _ in line_coords])
    right = np.array([(x, y) for _, _, _, x, y in line_coords])
    vertical_lines = []
    bad_line_mask = np.array([False] * len(lines))
    debug = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    for coords in [left, right]:
        masked = np.ma.MaskedArray(coords, np.ma.make_mask_none(coords.shape))
        while np.ma.count(masked) > 2:
            # fit line to coords
            xs, ys = masked[:, 0], masked[:, 1]
            [c0, c1] = np.ma.polyfit(xs, ys, 1)
            diff = c0 + c1 * xs - ys
            if np.linalg.norm(diff) > AH:
                masked.mask[np.ma.argmax(masked)] = True

        vertical_lines.append((c0, c1))
        bad_line_mask |= masked.mask

        cv2.line(debug, (0, c0), (im_w, c0 + c1 * im_w), (255, 0, 0), 3)

    debug_imwrite('vertical.png', debug)

    good_lines = np.where(~bad_line_mask)
    AB = good_lines.min()
    DC = good_lines.max()

    return AB, DC, bounds

def safe_rotate(im, angle):
    debug_imwrite('prerotated.png', im)
    im_h, im_w = im.shape[:2]
    if abs(angle) > math.pi / 4:
        print("warning: too much rotation")
        return im

    angle_deg = angle * 180 / math.pi
    print('rotating to angle:', angle_deg, 'deg')

    im_h_new = im_w * abs(math.sin(angle)) + im_h * math.cos(angle)
    im_w_new = im_h * abs(math.sin(angle)) + im_w * math.cos(angle)

    pad_h = int(math.ceil((im_h_new - im_h) / 2))
    pad_w = int(math.ceil((im_w_new - im_w) / 2))
    pads = ((pad_h, pad_h), (pad_w, pad_w)) + ((0, 0),) * (len(im.shape) - 2)

    padded = np.pad(im, pads, 'constant', constant_values=255)
    padded_h, padded_w = padded.shape[:2]
    matrix = cv2.getRotationMatrix2D((padded_w / 2, padded_h / 2), angle_deg, 1)
    result = cv2.warpAffine(padded, matrix, (padded_w, padded_h),
                            borderMode=cv2.BORDER_CONSTANT,
                            borderValue=255)
    debug_imwrite('rotated.png', result)
    return result

def fast_stroke_width(im):
    # im should be black-on-white. max stroke width 41.
    assert im.dtype == np.uint8 and is_bw(im)

    inv = im + 1
    inv_mask = im ^ 255
    dists = cv2.distanceTransform(inv, cv2.DIST_L2, 5)
    stroke_radius = min(20, int(math.ceil(np.percentile(dists, 95))))
    dists = 2 * dists + 1
    dists = dists.astype(np.uint8)
    rect = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    for idx in range(stroke_radius):
        dists = cv2.dilate(dists, rect)
        dists &= inv_mask

    dists_mask = (dists >= 41).astype(np.uint8) - 1
    dists &= dists_mask

    return dists

# only after rotation!
def fine_dewarp(out_0, im, AH, lines, underlines, all_letters, f_points):
    im_h, im_w = im.shape[:2]
    debug = out_0.copy()
    points = []
    y_offsets = []
    for line in lines:
        if len(line) < 10 or abs(line.fit_line().angle()) > 0.05: continue
        line_p = line.fit_line()
        line_p.draw(debug, thickness=1)
        # base_points = np.array([letter.base_point() for letter in line.letters])

        left_mid = [0, line_p(0)]
        right_mid = [im_w, line_p(im_w)]
        base_points = np.linspace(left_mid, right_mid, 20)

        median_y = np.median(base_points[:, 1])
        y_offsets.append(median_y - base_points[:, 1])
        points.append(base_points)

        # for underline in line.underlines:
        #     mid_contour = (underline.top_contour() + underline.bottom_contour()) / 2
        #     all_mid_points = np.stack([
        #         underline.x + np.arange(underline.w), mid_contour,
        #     ])
        #     mid_points = all_mid_points[:, ::4]
        #     points.append(mid_points)

        for p in base_points:
            pt = tuple(np.round(p).astype(int))
            cv2.circle(debug, (pt[0], int(median_y)), 8, lib.RED, -1)
            cv2.circle(debug, pt, 8, lib.GREEN, -1)
    lib.debug_imwrite('points.png', debug)

    # align fine dewarp
    left_bounds = np.array([l.original_letters[0].left_mid() for l in lines if len(l) > 10])
    right_bounds = np.array([l.original_letters[-1].right_mid() for l in lines if len(l) > 10])
    # x = my + b model weighted t
    class LinearXModel(object):
        def estimate(self, data):
            self.params = Poly.fit(data[:, 1], data[:, 0], 1, domain=[-1, 1])
            return True

        def residuals(self, data):
            return abs(self.params(data[:, 1]) - data[:, 0])
    
    vertical_lines = []
    points_in_vertical_liner = []
    for coords in [left_bounds, right_bounds]:
        model, inliers = ransac(coords, LinearXModel, 3, AH / 10.0)
        vertical_lines.append(model.params)
        ps = [p for p, inlier in zip(coords, inliers) if inlier]
        points_in_vertical_liner.append(ps)
    
    # x_offsets = []
    # for ps in points_in_vertical_liner:
    #     ps_array = np.array(ps)
    #     x_coords = ps_array[:, 0]
    #     first_x = x_coords[0]
    #     first_x = np.median(x_coords)
    #     x_offsets.append(x_coords - first_x)
    
    points = np.concatenate(points)
    y_offsets = np.concatenate(y_offsets)
    mesh = np.mgrid[:im_w, :im_h].astype(np.float32)
    xmesh, ymesh = mesh

    # points_in_vertical_liner = np.concatenate(points_in_vertical_liner)
    # x_offsets = np.concatenate(x_offsets)
    # x_offset_interp = interpolate.SmoothBivariateSpline(
    #     points_in_vertical_liner[:, 0], points_in_vertical_liner[:, 1], x_offsets.clip(-5, 5),
    #     s=4 * points_in_vertical_liner.shape[0]
    # )
    # xmesh -= x_offset_interp(xmesh, ymesh, grid=False).clip(-5, 5)
    # y_offset_interp = interpolate.griddata(points, y_offsets, xmesh, ymesh, method='nearest')
    # y_offset_interp = y_offset_interp.clip(-5, 5)
    # mesh[1] += y_offset_interp  # (mesh[0], mesh[1], grid=False)
    
    # y_offset_interp = interpolate.griddata((points[:, 0], points[:, 1]), 
    #                         y_offsets.clip(-AH, AH), 
    #                         (xmesh, ymesh), 
    #                         method='nearest')
    # ymesh -= y_offset_interp
    
    y_offset_interp = interpolate.SmoothBivariateSpline(
        points[:, 0], points[:, 1], y_offsets.clip(-AH, AH),
        s=4 * points.shape[0]
    )
    ymesh -= y_offset_interp(xmesh, ymesh, grid=False).clip(-AH, AH)

    conv_xmesh, conv_ymesh = cv2.convertMaps(xmesh, ymesh, cv2.CV_16SC2)
    
    out = cv2.remap(out_0, conv_xmesh, conv_ymesh,
                    interpolation=cv2.INTER_LINEAR,
                    borderValue=(0,0,0)).T
    
    out = np.transpose(out, (1, 2, 0))

    # debug = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
    # for line in lines:
    #     base_points = np.array([letter.base_point() for letter in line.letters[1:-1]])
    #     base_points[:, 1] -= y_offset_interp(base_points[:, 0], base_points[:, 1], grid=False)
    #     Line.fit(base_points).draw(debug, thickness=1)
    # cv2.imwrite('corrected_line.png', debug)

    control_points = []
    for p in vertical_lines:
        control_points.append([p(0), 0])
        control_points.append([p(im_h), im_h])

    page_pad_left = 3*AH   #max(min(abs(control_points[0][0]), abs(control_points[1][0])), 2*AH)
    page_pad_right = 3*AH  #max(min(abs(control_points[2][0] - im_w), abs(control_points[3][0] - im_w)), 2*AH)
    control_points[0][0] -= page_pad_left
    control_points[1][0] -= page_pad_left
    control_points[2][0] += page_pad_right
    control_points[3][0] += page_pad_right
    pts1 = np.float32(control_points)
    w = int(control_points[2][0] - control_points[0][0])
    pts0 = np.float32([[0,0],[0,im_h],[w,0],[w,im_h]])
    
    M_L = cv2.getPerspectiveTransform(pts1,pts0)
    dst = cv2.warpPerspective(out,M_L,(w,im_h),borderValue=(0,0,0))
    #extract textline upon hand drawn line
    bounding_boxes_with_flags_array = None

    if f_points:
        pre_lines = []
        for p in f_points:
            #find most closest text line
            if p[0] < dst.shape[1] / 2:
                bounds_y = np.array([l.original_letters[0].left_mid()[1] for l in lines])
            else:
                bounds_y = np.array([l.original_letters[0].right_mid()[1] for l in lines])
            diff = np.abs(bounds_y - p[1])
            pre_lines.append([np.argmin(diff), p[1]-bounds_y[np.argmin(diff)]])
        
        if len(pre_lines) == 1:
            pre_line = pre_lines[0]
            point_1 = lines[pre_line[0]][0].left_top()
            point_2 = lines[pre_line[0]][-1].right_top()
            point_3 = lines[pre_line[0]][-1].right_bot()
            point_4 = lines[pre_line[0]][0].left_bot()
            all_points_array = np.array([
                                    conv_xmesh[point_1[0], point_1[1]],
                                    conv_xmesh[point_2[0], point_2[1]],
                                    conv_xmesh[point_3[0], point_3[1]],
                                    conv_xmesh[point_4[0], point_4[1]],
                                    ])
        
            points_homogeneous = np.hstack((all_points_array, np.ones((all_points_array.shape[0], 1))))
            transformed_points_homogeneous = M_L @ points_homogeneous.T
            transformed_points = transformed_points_homogeneous[:2] / transformed_points_homogeneous[2]
            transformed_points = transformed_points.T.reshape(-1, 4, 2)
            transformed_points[:, :, 0] = np.clip(transformed_points[:, :, 0], 0, dst.shape[1])
            transformed_points[:, :, 1] = np.clip(transformed_points[:, :, 1], 0, dst.shape[0])
            edge = AH / 5
            y_min = max(int(np.min(transformed_points[0][:, 1]) - edge), 0)
            y_max = min(int(np.max(transformed_points[0][:, 1]) + edge), dst.shape[0])
            bounding_boxes_with_flags_array = np.array([[page_pad_left, y_min, dst.shape[1]-page_pad_right, y_max, 20]])
        elif len(pre_lines) == 2:
            all_points = []
            bounding_boxes = []
            num_letters = sum(len(line) for line in lines[pre_lines[0][0]:pre_lines[1][0]])
            print('Number of letters:', num_letters, abs(f_points[1][1] - f_points[0][1]))
            if num_letters > abs(f_points[1][1] - f_points[0][1]) / AH * 5:
                for _, line in enumerate(lines[pre_lines[0][0]:pre_lines[1][0]]):
                    point_1 = line[0].left_top()
                    point_2 = line[-1].right_top()
                    point_3 = line[-1].right_bot()
                    point_4 = line[0].left_bot()
                    points = np.array([
                                conv_xmesh[point_1[0], point_1[1]],
                                conv_xmesh[point_2[0], point_2[1]],
                                conv_xmesh[point_3[0], point_3[1]],
                                conv_xmesh[point_4[0], point_4[1]],
                                ])
                    all_points.append(points)
                all_points_array = np.vstack(all_points)
                points_homogeneous = np.hstack((all_points_array, np.ones((all_points_array.shape[0], 1))))
                transformed_points_homogeneous = M_L @ points_homogeneous.T
                transformed_points = transformed_points_homogeneous[:2] / transformed_points_homogeneous[2]
                transformed_points = transformed_points.T.reshape(-1, 4, 2)
                transformed_points[:, :, 0] = np.clip(transformed_points[:, :, 0], 0, dst.shape[1])
                transformed_points[:, :, 1] = np.clip(transformed_points[:, :, 1], 0, dst.shape[0])

                for points in transformed_points:
                    x_min = int(np.min(points[:4, 0]) - AH)
                    y_min = int(np.min(points[:4, 1]) - AH / 5)
                    x_max = int(np.max(points[:4, 0]) + AH)
                    y_max = int(np.max(points[:4, 1]) + AH / 5)
                    # x_values = [letter.base_point()[0] for letter in all_letters if y_min <= letter.base_point()[1] <= y_max]
                    if (bounding_boxes and 
                        bounding_boxes[-1][2] >= dst.shape[1] - page_pad_right - AH/2 and 
                        x_min <=  page_pad_left + AH / 2):
                        bounding_boxes.append((max(page_pad_left, x_min), y_min, min(dst.shape[1]-page_pad_right, x_max), y_max, 21))
                    else:
                        bounding_boxes.append((max(page_pad_left, x_min), y_min, min(dst.shape[1]-page_pad_right, x_max), y_max, 20))
            else:
                all_points_array = np.vstack(f_points)
                points_homogeneous = np.hstack((all_points_array, np.ones((all_points_array.shape[0], 1))))
                transformed_points_homogeneous = M_L @ points_homogeneous.T
                transformed_points = transformed_points_homogeneous[:2] / transformed_points_homogeneous[2]
                transformed_points = transformed_points.T.reshape(-1, 2, 2)
                transformed_points[:, :, 0] = np.clip(transformed_points[:, :, 0], 0, dst.shape[1])
                transformed_points[:, :, 1] = np.clip(transformed_points[:, :, 1], 0, dst.shape[0])
                bounding_boxes.append((page_pad_left, int(transformed_points[0,0,1]), dst.shape[1]-page_pad_right, int(transformed_points[0,1,1]), 2))

            bounding_boxes_with_flags_array = np.array(bounding_boxes)
            # bounding_boxes_with_flags_array[:, [0, 2]] = np.clip(bounding_boxes_with_flags_array[:, [0, 2]], 0, dst.shape[1])
            # bounding_boxes_with_flags_array[:, [1, 3]] = np.clip(bounding_boxes_with_flags_array[:, [1, 3]], 0, dst.shape[0])

    if underlines:
        all_points = []
        for underline in underlines:
            idx, start, end, left_mid, right_mid = underline
            point_1 = lines[idx][start].left_top()
            point_2 = lines[idx][end].right_top()
            point_3 = lines[idx][end].right_bot()
            point_4 = lines[idx][start].left_bot()
            points = np.array([
                        conv_xmesh[point_1[0], point_1[1]],
                        conv_xmesh[point_2[0], point_2[1]],
                        conv_xmesh[point_3[0], point_3[1]],
                        conv_xmesh[point_4[0], point_4[1]],
                        conv_xmesh[int(left_mid[0]), int(left_mid[1])],
                        conv_xmesh[min(int(right_mid[0]), len(conv_xmesh)-1), int(right_mid[1])],
                        ])
            all_points.append(points)

        all_points_array = np.vstack(all_points)
        points_homogeneous = np.hstack((all_points_array, np.ones((all_points_array.shape[0], 1))))
        transformed_points_homogeneous = M_L @ points_homogeneous.T
        transformed_points = transformed_points_homogeneous[:2] / transformed_points_homogeneous[2]
        transformed_points = transformed_points.T.reshape(-1, 6, 2)
        transformed_points[:, :, 0] = np.clip(transformed_points[:, :, 0], 0, dst.shape[1])
        transformed_points[:, :, 1] = np.clip(transformed_points[:, :, 1], 0, dst.shape[0])

        bounding_boxes = []
        for points in transformed_points:
            edge = AH / 5
            x_min = int(np.min(points[:, 0]) - edge)
            y_min = int(np.min(points[:4, 1]) - edge)
            x_max = int(np.max(points[:, 0]) + edge)
            y_max = int(np.max(points[:4, 1]) + edge)
            bounding_boxes.append((x_min, y_min, x_max, y_max))
        bounding_boxes_array = np.array(bounding_boxes)
        bounding_boxes_array[:, [0, 2]] = np.clip(bounding_boxes_array[:, [0, 2]], 0, dst.shape[1])
        bounding_boxes_array[:, [1, 3]] = np.clip(bounding_boxes_array[:, [1, 3]], 0, dst.shape[0])

        #paragraph continuity check
        continuous = [0]
        for i in range(len(underlines) - 1):
            current = underlines[i]
            next_underline = underlines[i + 1]
            current_idx, current_start, current_end, _, _ = current
            next_idx, next_start, next_end, _, _ = next_underline
            _, _, _, _, current_left_mid, current_right_mid = transformed_points[i]
            _, _, _, _, next_left_mid, next_right_mid = transformed_points[i+1]
            if (current_idx == next_idx - 1 and 
                # current_end == len(lines[current_idx]) - 1 and 
                # next_start == 0):
                current_right_mid[0] > dst.shape[1] - page_pad_right - AH / 2 and 
                next_left_mid[0] < page_pad_left + AH / 2):
                continuous.append(1)
            else:
                continuous.append(0)

        if bounding_boxes_with_flags_array is None:
            bounding_boxes_with_flags_array = np.column_stack((bounding_boxes_array, continuous))
        else:
            bounding_boxes_with_flags_array = np.concatenate((
                                        bounding_boxes_with_flags_array, 
                                        np.column_stack((bounding_boxes_array, continuous))), axis=0)

    if lib.debug:
        if bounding_boxes_with_flags_array is not None:
            for box in bounding_boxes_with_flags_array:
                x_min, y_min, x_max, y_max, _ = box
                cropped_image = dst[y_min:y_max, x_min:x_max]
                save_path = f"textline_{x_min}_{y_min}.png"
                lib.debug_imwrite(save_path, cropped_image)

    return dst, bounding_boxes_with_flags_array

def masked_mean_std(data, mask):
    mask_sum = np.count_nonzero(mask)
    mean = data.sum() / mask_sum
    data = data.astype(np.float64, copy=False)
    data_dev = np.zeros(data.shape, dtype=np.float64)
    np.subtract(data, mean, out=data_dev, where=mask.astype(bool, copy=False))
    std = np.sqrt(np.square(data_dev).sum() / mask_sum)
    return mean, std

def remove_stroke_outliers(im, lines, k=1.0):
    stroke_widths = fast_stroke_width(im)
    if lib.debug:
        lib.debug_imwrite('strokes.png', lib.normalize_u8(stroke_widths.clip(0, 10)))

    mask = np.zeros(im.shape, dtype=np.uint8)
    for line in lines:
        for letter in line:
            sliced = letter.crop().apply(mask)
            sliced |= letter.raster()

    lib.debug_imwrite('letter_mask.png', -mask)

    masked_strokes = stroke_widths.copy()
    masked_strokes &= -mask

    strokes_mean, strokes_std = masked_mean_std(masked_strokes, mask)
    if lib.debug:
        print('overall: mean:', strokes_mean, 'std:', strokes_std)

    debug = cv2.cvtColor(im, cv2.COLOR_GRAY2RGB)
    new_lines = []
    for line in lines:
        if len(line) <= 1: continue
        good_letters = []
        for letter in line:
            crop = letter.crop()
            if not crop.nonempty(): continue

            raster = letter.raster()
            sliced_strokes = crop.apply(stroke_widths).copy()
            sliced_strokes &= lib.bool_to_u8(raster)

            mean, std = masked_mean_std(sliced_strokes, raster)
            if mean < strokes_mean - k * strokes_std:
                if lib.debug:
                    print('skipping {:4d} {:4d} {:.03f} {:.03f}'.format(
                        letter.x, letter.y, mean, std,
                    ))
                    letter.box(debug, color=lib.RED)
            else:
                if lib.debug: letter.box(debug, color=lib.GREEN)
                good_letters.append(letter)

        if good_letters:
            new_lines.append(TextLine(good_letters, underlines=line.underlines))

    lib.debug_imwrite("stroke_filter.png", debug)

    return new_lines

def filter_spacing_deviation(im, AH, lines):
    new_lines = []

    debug = cv2.cvtColor(im, cv2.COLOR_GRAY2RGB)
    for line in lines:
        spacings = np.array([l2.x - l1.right() for l1, l2 in zip(line, line[1:])])
        # print("spacing", spacings.std())
        if spacings.std() > AH / 1.0:
            line.crop().draw(debug, color=lib.RED)
        else:
            line.crop().draw(debug, color=lib.GREEN)
            new_lines.append(line)

    lib.debug_imwrite("spacing_filter.png", debug)

    return new_lines
