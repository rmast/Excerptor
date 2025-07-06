import cv2
import os
import sys

def resize_to_match_aspect(img, ref_shape):
    h, w = ref_shape[:2]
    aspect_in = img.shape[1] / img.shape[0]
    aspect_ref = w / h
    if abs(aspect_in - aspect_ref) < 1e-2:
        return img
    if aspect_in > aspect_ref:
        new_w = int(img.shape[0] * aspect_ref)
        resized = cv2.resize(img, (new_w, img.shape[0]), interpolation=cv2.INTER_CUBIC)
    else:
        new_h = int(img.shape[1] / aspect_ref)
        resized = cv2.resize(img, (img.shape[1], new_h), interpolation=cv2.INTER_CUBIC)
    return resized

if __name__ == "__main__":
    input_img = sys.argv[1]      # origineel bestand (input)
    dewarped_img = sys.argv[2]   # reeds gedewarped bestand (output van vorige run)
    out_img = sys.argv[3]        # doelbestand

    ref = cv2.imread(input_img)
    img = cv2.imread(dewarped_img)
    if ref is None or img is None:
        print(f"Error: kon {input_img} of {dewarped_img} niet openen")
        sys.exit(1)
    resized = resize_to_match_aspect(img, ref.shape)
    cv2.imwrite(out_img, resized)
