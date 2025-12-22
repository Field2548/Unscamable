from paddleocr import PaddleOCR

# Initialize PaddleOCR (This will automatically download the PP-OCRv5 model)
# lang='en' for English, 'ch' for Chinese, etc.
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False
)

# Run OCR on an image URL (or replace with a local file path like './my_image.jpg')
img_path = "https://paddle-model-ecology.bj.bcebos.com/paddlex/imgs/demo_image/general_ocr_002.png"
result = ocr.predict(input=img_path)

# Print results
for res in result:
    res.print()
    # Optional: Save results to files
    # res.save_to_img("output")
    # res.save_to_json("output")
