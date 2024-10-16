import os
import glob
import cv2
import numpy as np
import onnxruntime
from ultralytics import YOLO
from rapidocr_onnxruntime import RapidOCR
from argparse import ArgumentParser
from rebook.spliter import book_spliter
from rebook.dewarp import go_dewarp

def ill_correct(image):
    im = image.astype(np.float32) / 255.0
    gauss = cv2.GaussianBlur(im, (201, 201), 0)
    dst_0 = im / (gauss + 1e-10) * 255
    dst_0 = np.clip(dst_0, 0, 255).astype(np.uint8)

    x = np.arange(256)
    y = 1/256 * (x) ** 2
    curve = np.clip(y, 0, 255).astype(np.uint8)
    dst_1 = cv2.LUT(dst_0, curve)

    gray = cv2.cvtColor(dst_1, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h, w = binary.shape
    for contour in contours:
        x, y, contour_w, contour_h = cv2.boundingRect(contour)
        if x == 0 or y == 0 or (x + contour_w) == w or (y + contour_h) == h:
            cv2.drawContours(dst_1, [contour], -1, (255, 255, 255), thickness=cv2.FILLED)
            cv2.drawContours(dst_1, [contour], -1, (255, 255, 255), thickness=5)

    return dst_1

def white_balance_correct(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    img = cv2.convertScaleAbs(image, alpha=180/mean_brightness, beta=0)

    (b, g, r) = cv2.split(img)
    b_avg = np.mean(b)
    g_avg = np.mean(g)
    r_avg = np.mean(r)
    avg_gray = (b_avg + g_avg + r_avg) / 3
    b_scale = avg_gray / b_avg
    g_scale = avg_gray / g_avg
    r_scale = avg_gray / r_avg
    b = cv2.convertScaleAbs(b * b_scale)
    g = cv2.convertScaleAbs(g * g_scale)
    r = cv2.convertScaleAbs(r * r_scale)
    balanced_img = cv2.merge([b, g, r])

    return balanced_img

def hand_landmark(image):
    hand = PoseTracker(
    Hand,
    tracking=False,
    det_frequency=7,
    to_openpose=False,
    mode='lightweight',  # balanced, performance, lightweight
    backend='onnxruntime',
    device='cpu')

    keypoints, scores = hand(image)
    threshold = 0.6
    hands_lm = []
    for keypoint, score in zip(keypoints, scores):
        if score[4] > threshold:
            hands_lm.append([keypoint[4][0], keypoint[4][1]]) 
        if score[8] > threshold:
            hands_lm.append([keypoint[8][0], keypoint[8][1]]) 

    return hands_lm

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        help=\
            'Debug, keep processing files, print infomations',
    )
    parser.add_argument(
        '-ms',
        '--model_seg',
        type=str,
        default='model/yolov8l-seg.pt',
        help='Model file path for YOLO segment.',
    )
    parser.add_argument(
        '-ha',
        '--hand_mark',
        action='store_true',
        help=\
            'Recognize hands or not.',
    )
    parser.add_argument(
        '-l',
        '--line_mark',
        action='store_true',
        help=\
            'Recognize underlines or not.',
    )
    parser.add_argument(
        '-wb',
        '--white_balance',
        action='store_true',
        help=\
            'Perform white balance correction on the cropped image. '+
            'or '+
            'Perform bleaching on the cropped image.',
    )
    parser.add_argument(
        '-i',
        '--input_folder',
        type=str,
        default='book',
        help='Put original image in this folder.',
    )
    parser.add_argument(
        '-o',
        '--output_folder',
        type=str,
        default='dewarped_img',
        help='Dewarped image will be put in this folder.',
    )
    parser.add_argument(
        '-a',
        '--archive_folder',
        type=str,
        default='original_img',
        help='Archive original image in this folder.',
    )
    parser.add_argument(
        '-n',
        '--note_name',
        type=str,
        default='note.md',
        help='Model file path for YOLO segment.',
    )
    args = parser.parse_args()
    debug: bool = args.debug
    model_seg: str = args.model_seg
    hand_mark: bool = args.hand_mark
    line_mark: bool = args.line_mark
    white_balance: bool = args.white_balance
    input_folder: str = args.input_folder
    output_folder: str = args.output_folder
    archive_folder: str = args.archive_folder
    note_name: str = args.note_name
    
    if hand_mark:
        from rtmlib import Hand, PoseTracker, draw_skeleton

    model = YOLO(model_seg)
    ocr = RapidOCR()
    os.makedirs(archive_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)

    image_paths = glob.glob(os.path.join(input_folder, '*.jpg'))
    image_paths += glob.glob(os.path.join(input_folder, '*.jpeg'))
    image_paths += glob.glob(os.path.join(input_folder, '*.png'))
    if image_paths:
        with open(note_name, 'a', encoding='utf-8') as note_file:
            for image_path in image_paths:
                frame = cv2.imread(image_path)
                f_points = []
                if hand_mark:
                    f_points = hand_landmark(frame)
                results = model(frame)
                re = book_spliter(frame, results, f_points)
                
                if re is not None:
                    book_left, book_right, ctr_l, ctr_r, f_points_l, f_points_r = re
                    if book_left.shape[1] > ctr_l[0]:
                        img_dewarped = go_dewarp(book_left, ctr_l, debug=debug, f_points=f_points_l)
                    else:
                        img_dewarped = go_dewarp(book_right, ctr_r, debug=debug, f_points=f_points_r)

                    img_dewarped_ill = ill_correct(img_dewarped[0][0])
                    
                    original_filename = os.path.basename(image_path)
                    cv2.imwrite(os.path.join(archive_folder, original_filename), frame)
                    dewarped_filename = original_filename.replace('.', '_dewarped.')
                    cropped_pic_filename = original_filename.replace('.', '_dewarped_pic.')
                    cv2.imwrite(os.path.join(output_folder, dewarped_filename), img_dewarped_ill)

                    boxes = img_dewarped[0][1]
                    text_lines = []
                    cropped_img = None
                    if boxes is not None:
                        for box in boxes:
                            x_min, y_min, x_max, y_max, cont_flag = box

                            if cont_flag == 1 and text_lines and line_mark:
                                ocr_results, _ = ocr(img_dewarped_ill[y_min:y_max, x_min:x_max], use_det=False, use_cls=False, use_rec=True)
                                text_lines[-1] += ocr_results[0][0]
                            elif cont_flag == 0 and line_mark:
                                ocr_results, _ = ocr(img_dewarped_ill[y_min:y_max, x_min:x_max], use_det=False, use_cls=False, use_rec=True)
                                text_lines.append(ocr_results[0][0])

                            if cont_flag == 21 and text_lines and hand_mark:
                                ocr_results, _ = ocr(img_dewarped_ill[y_min:y_max, x_min:x_max], use_det=False, use_cls=False, use_rec=True)
                                text_lines[-1] += ocr_results[0][0]
                            elif cont_flag == 20 and hand_mark:
                                ocr_results, _ = ocr(img_dewarped_ill[y_min:y_max, x_min:x_max], use_det=False, use_cls=False, use_rec=True)
                                text_lines.append(ocr_results[0][0])

                            elif cont_flag == 2:
                                if white_balance:
                                    cropped_img = white_balance_correct(img_dewarped[0][0])[y_min:y_max, x_min:x_max]
                                else:
                                    cropped_img = img_dewarped_ill[y_min:y_max, x_min:x_max]
                                cv2.imwrite(os.path.join(output_folder, cropped_pic_filename), cropped_img)

                    #extract page number
                    dets, _ = ocr(img_dewarped_ill, use_det=True, use_cls=False, use_rec=False)
                    dets = dets[:3] + dets[-3:]
                    ocrs = []
                    dets = np.array(dets)
                    for det in dets:
                        x_min = int(np.min(det[:, 0]))
                        y_min = int(np.min(det[:, 1]))
                        x_max = int(np.max(det[:, 0]))
                        y_max = int(np.max(det[:, 1]))
                        re = ocr(img_dewarped_ill[y_min:y_max,x_min:x_max], use_det=False, use_cls=False, use_rec=True)
                        ocrs.append(re)
                    best_text = ''
                    num_percent = 0
                    for re in ocrs:
                        text = re[0][0][0]
                        if 0 < len(text) <= 6:
                            digit_count = sum(1 for t in text if t.isdigit())
                            if digit_count / len(text) > num_percent:
                                best_text = text
                                num_percent = digit_count / len(text)
                    page_number = ''.join(t for t in best_text if t.isdigit())
                    note_file.write(f'> Page {page_number}\n')
                    #text and cropped image
                    for line in text_lines:
                        note_file.write(f'> - {line}\n')
                    if cropped_img is not None:
                        note_file.write(f'![{cropped_pic_filename}]({output_folder}/{cropped_pic_filename})\n\n')
                    note_file.write(f'![{dewarped_filename}]({output_folder}/{dewarped_filename})\n\n')