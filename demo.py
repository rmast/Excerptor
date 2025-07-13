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
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed

def ill_correct(image: np.ndarray) -> np.ndarray:
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

def white_balance_correct(image: np.ndarray) -> np.ndarray:
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

def hand_landmark(image: np.ndarray) -> list[list[float]]:
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

# Voeg deze hulpfunctie toe om de aspectratio van de invoer te bewaren
def resize_to_match_aspect(img: np.ndarray, ref_shape: tuple[int, int, int]) -> np.ndarray:
    """Resize img zodat aspectratio overeenkomt met ref_shape (h, w)."""
    h, w = ref_shape[:2]
    aspect_in = img.shape[1] / img.shape[0]
    aspect_ref = w / h
    if abs(aspect_in - aspect_ref) < 1e-2:
        return img  # al goed genoeg
    # Bepaal nieuwe grootte met behoud van aspectratio
    if aspect_in > aspect_ref:
        # img is breder, pas breedte aan
        new_w = int(img.shape[0] * aspect_ref)
        resized = cv2.resize(img, (new_w, img.shape[0]), interpolation=cv2.INTER_CUBIC)
    else:
        # img is hoger, pas hoogte aan
        new_h = int(img.shape[1] / aspect_ref)
        resized = cv2.resize(img, (img.shape[1], new_h), interpolation=cv2.INTER_CUBIC)
    return resized

def process_image(image_path: str, args_dict: dict) -> tuple[str, list[str]]:
    import cv2
    import numpy as np
    import traceback
    from rapidocr_onnxruntime import RapidOCR
    from rebook.dewarp import go_dewarp
    from rebook.spliter import book_spliter

    debug: bool = args_dict['debug']
    model_seg: str = args_dict['model_seg']
    hand_mark: bool = args_dict['hand_mark']
    line_mark: bool = args_dict['line_mark']
    white_balance: bool = args_dict['white_balance']
    visualize_textlines: bool = args_dict['visualize_textlines']
    archive_folder: str = args_dict['archive_folder']
    output_folder: str = args_dict['output_folder']
    note_name: str = args_dict['note_name']
    scantailor_split: bool = args_dict['scantailor_split']
    split_pages: bool = args_dict['split_pages']

    if hand_mark:
        from rtmlib import Hand, PoseTracker, draw_skeleton
    if not scantailor_split:
        from ultralytics import YOLO
        model = YOLO(model_seg)
    ocr = RapidOCR()

    original_filename: str = os.path.basename(image_path)
    base, ext = os.path.splitext(original_filename)
    result_lines: list[str] = []
    try:
        frame = cv2.imread(image_path)
        if frame is None:
            result_lines.append(f'Error: kon {image_path} niet openen\n')
            return base, result_lines
        input_shape: tuple[int, int, int] = frame.shape
        f_points: list = []
        if scantailor_split:
            book_left: np.ndarray = frame
            book_right: None = None
            ctr_l: None = None
            ctr_r: None = None
            f_points_l: list = []
            f_points_r: list = []
            re = (book_left, book_right, ctr_l, ctr_r, f_points_l, f_points_r)
        else:
            if hand_mark:
                f_points = hand_landmark(frame)
            results = model(frame)
            re = book_spliter(frame, results, f_points)
        if re is not None:
            book_left, book_right, ctr_l, ctr_r, f_points_l, f_points_r = re
            if scantailor_split:
                pages: list[tuple[str, np.ndarray, None, list]] = [
                    ("L", book_left,  ctr_l, f_points_l),
                ]
            else:
                pages: list[tuple[str, np.ndarray, object, list]] = [
                    ("L", book_left,  ctr_l, f_points_l),
                    ("R", book_right, ctr_r, f_points_r),
                ]
            for side, page_im, page_ctr, page_points in pages:
                if page_im is None or getattr(page_im, "size", 0) == 0:
                    result_lines.append(f'{image_path} [{side}]: splitter gaf lege pagina; overslaan')
                    continue
                try:
                    img_dewarped = go_dewarp(
                        page_im, page_ctr,
                        debug=debug,
                        f_points=page_points,
                        split=split_pages
                    )
                    dewarped_img: np.ndarray = img_dewarped[0][0]
                    dewarped_img = resize_to_match_aspect(dewarped_img, input_shape)
                    img_dewarped_ill: np.ndarray = ill_correct(dewarped_img)
                    dewarped_filename: str = f"{base}_{side}_dewarped{ext}"
                    cropped_pic_filename: str = f"{base}_{side}_dewarped_pic{ext}"
                    cv2.imwrite(os.path.join(archive_folder, original_filename), frame)
                    cv2.imwrite(os.path.join(output_folder, dewarped_filename), img_dewarped_ill)
                    boxes = img_dewarped[0][1]
                    
                    # Visualiseer textlines op originele afbeelding
                    if visualize_textlines and boxes is not None:
                        textlines_filename = f"{base}_{side}_textlines{ext}"
                        textlines_path = os.path.join(output_folder, textlines_filename)
                        visualize_textlines_on_image(page_im, boxes, textlines_path)
                    
                    text_lines: list[str] = []
                    cropped_img: np.ndarray | None = None
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
                                    cropped_img = white_balance_correct(dewarped_img)[y_min:y_max, x_min:x_max]
                                else:
                                    cropped_img = img_dewarped_ill[y_min:y_max, x_min:x_max]
                                cv2.imwrite(os.path.join(output_folder, cropped_pic_filename), cropped_img)
                    dets, _ = ocr(img_dewarped_ill, use_det=True, use_cls=False, use_rec=False)
                    if dets is not None and len(dets) > 0:
                        dets = dets[:3] + dets[-3:]
                        ocrs: list = []
                        dets = np.array(dets)
                        for det in dets:
                            x_min = int(np.min(det[:, 0]))
                            y_min = int(np.min(det[:, 1]))
                            x_max = int(np.max(det[:, 0]))
                            y_max = int(np.max(det[:, 1]))
                            reocr = ocr(img_dewarped_ill[y_min:y_max,x_min:x_max], use_det=False, use_cls=False, use_rec=True)
                            ocrs.append(reocr)
                        best_text: str = ''
                        num_percent: float = 0
                        for reocr in ocrs:
                            text = reocr[0][0][0]
                            if 0 < len(text) <= 6:
                                digit_count = sum(1 for t in text if t.isdigit())
                                if len(text) > 0 and digit_count / len(text) > num_percent:
                                    best_text = text
                                    num_percent = digit_count / len(text)
                        page_number = ''.join(t for t in best_text if t.isdigit())
                    else:
                        page_number = ''
                    result_lines.append(f'> Page {page_number}\n')
                    for line in text_lines:
                        result_lines.append(f'> - {line}\n')
                    if cropped_img is not None:
                        result_lines.append(f'![{cropped_pic_filename}]({output_folder}/{cropped_pic_filename})\n\n')
                    
                    # Voeg textlines-visualisatie toe aan output
                    if visualize_textlines and boxes is not None:
                        textlines_filename = f"{base}_{side}_textlines{ext}"
                        result_lines.append(f'![{textlines_filename}]({output_folder}/{textlines_filename})\n\n')
                    
                    result_lines.append(f'![{dewarped_filename}]({output_folder}/{dewarped_filename})\n\n')
                except Exception as e:
                    result_lines.append(f'Error processing {image_path} [{side}]: dewarp faalde met {e.__class__.__name__}: {e}\n')
                    traceback.print_exc()
                    continue
    except Exception as e:
        result_lines.append(f'Error processing {image_path}: {e}\n')
    return base, result_lines

def visualize_textlines_on_image(image: np.ndarray, boxes: list, output_path: str) -> None:
    """
    Visualiseer de gedetecteerde textlines op het originele beeld.
    
    Args:
        image: Het originele beeld (numpy array)
        boxes: Lijst van bounding boxes [x_min, y_min, x_max, y_max, cont_flag]
        output_path: Pad waar de visualisatie wordt opgeslagen
    """
    if boxes is None or len(boxes) == 0:
        return
    
    # Maak een kopie van het beeld voor visualisatie
    vis_image = image.copy()
    
    # Kleuren voor verschillende types
    colors = {
        0: (0, 255, 0),    # Groen voor normale textlines
        1: (0, 255, 255),  # Geel voor voortzetting textlines
        2: (255, 0, 0),    # Blauw voor afbeeldingen
        20: (255, 0, 255), # Magenta voor hand-gemarkeeerde tekst
        21: (255, 0, 255), # Magenta voor hand-gemarkeeerde tekst (voortzetting)
    }
    
    # Teken alle bounding boxes
    for box in boxes:
        x_min, y_min, x_max, y_max, cont_flag = box
        color = colors.get(cont_flag, (128, 128, 128))  # Grijs als fallback
        
        # Teken rechthoek
        cv2.rectangle(vis_image, (x_min, y_min), (x_max, y_max), color, 2)
        
        # Voeg label toe
        label = f"T{cont_flag}"
        cv2.putText(vis_image, label, (x_min, y_min - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    # Sla visualisatie op
    cv2.imwrite(output_path, vis_image)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        "-sp", "--split-pages",
        action="store_true",
        help="Splits tweepagina‑scans in links/rechts en dewarped beide."
    )
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
    parser.add_argument(
        '--scantailor-split',
        action='store_true',
        help='Interpreteer elke afbeelding als reeds gesplitste pagina (Scantailor output).'
    )
    parser.add_argument(
        '-vt',
        '--visualize_textlines',
        action='store_true',
        help='Save visualization of detected textlines on original image.',
    )
    args = parser.parse_args()
    debug: bool = args.debug
    model_seg: str = args.model_seg
    hand_mark: bool = args.hand_mark
    line_mark: bool = args.line_mark
    white_balance: bool = args.white_balance
    visualize_textlines: bool = args.visualize_textlines
    input_folder: str = args.input_folder
    output_folder: str = args.output_folder
    archive_folder: str = args.archive_folder
    note_name: str = args.note_name
    scantailor_split: bool = args.scantailor_split

    if hand_mark:
        from rtmlib import Hand, PoseTracker, draw_skeleton

    args_dict = {
        'debug': debug,
        'model_seg': model_seg,
        'hand_mark': hand_mark,
        'line_mark': line_mark,
        'white_balance': white_balance,
        'visualize_textlines': visualize_textlines,
        'archive_folder': archive_folder,
        'output_folder': output_folder,
        'note_name': note_name,
        'scantailor_split': scantailor_split,
        'split_pages': args.split_pages,
    }
    image_paths = glob.glob(os.path.join(input_folder, '*.jpg'))
    image_paths += glob.glob(os.path.join(input_folder, '*.jpeg'))
    image_paths += glob.glob(os.path.join(input_folder, '*.png'))
    image_paths += glob.glob(os.path.join(input_folder, '*.tif'))
    if image_paths:
        with open(note_name, 'a', encoding='utf-8') as note_file:
            # Beperk het aantal workers als je CUDA gebruikt
            max_workers = 5  # Of 1 als je zeker wilt zijn van geen OOM
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(process_image, image_path, args_dict) for image_path in image_paths]
                for future in as_completed(futures):
                    base, result_lines = future.result()
                    note_file.write(f'Verwerk bestand {base}\n')
                    for line in result_lines:
                        note_file.write(line)
            # Beperk het aantal workers als je CUDA gebruikt
            max_workers = 5  # Of 1 als je zeker wilt zijn van geen OOM
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(process_image, image_path, args_dict) for image_path in image_paths]
                for future in as_completed(futures):
                    base, result_lines = future.result()
                    note_file.write(f'Verwerk bestand {base}\n')
                    for line in result_lines:
                        note_file.write(line)
