# Extract underlined text or text marked by hands from physical books.

Process: `segment`->`split`->`dewarp`->`ocr`

## Algorithm

For details: [rebook](/rebook/README.md)

## Building

Requirements: Numpy/Scipy, OpenCV (with python bindings), Cython, ultralytics, RapidOCR

```
pip install -r requirements.txt
```

```
python setup.py build_ext
```

## Running

```
python demo.py -ha -l
```

```
options:
  -h, --help            show this help message and exit
  -d, --debug           Debug, keep processing files, print infomations
  -ms MODEL_SEG, --model_seg MODEL_SEG
                        Model file path for YOLO segment.
  -ha, --hand_mark      Recognize hands or not.
  -l, --line_mark       Recognize underlines or not.
  -wb, --white_balance  Perform white balance correction on the cropped image. or  
                        Perform bleaching on the cropped image.
  -i INPUT_FOLDER, --input_folder INPUT_FOLDER
                        Put original image in this folder.
  -o OUTPUT_FOLDER, --output_folder OUTPUT_FOLDER
                        Dewarped image will be put in this folder.
  -a ARCHIVE_FOLDER, --archive_folder ARCHIVE_FOLDER
                        Archive original image in this folder.
  -n NOTE_NAME, --note_name NOTE_NAME
                        Model file path for YOLO segment.
```

## Credits

- [phulin/rebook](https://github.com/phulin/rebook)