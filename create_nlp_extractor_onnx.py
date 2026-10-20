import os
import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType
import shutil

WORKSPACE = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass"
RAW_ONNX = os.path.join(WORKSPACE, "test_minilm.onnx")
QUANT_ONNX = os.path.join(WORKSPACE, "nlp_extractor_int8.onnx")
DEST_EXT = os.path.join(WORKSPACE, "fb_following_scraper", "nlp_extractor.onnx")

def process():
    if not os.path.exists(RAW_ONNX):
        print(f"Waiting for {RAW_ONNX} to be created...")
        return
    
    print(f"[*] Quantizing {RAW_ONNX} to INT8...")
    quantize_dynamic(
        RAW_ONNX,
        QUANT_ONNX,
        weight_type=QuantType.QUInt8
    )
    
    raw_size = os.path.getsize(RAW_ONNX) / (1024 * 1024)
    quant_size = os.path.getsize(QUANT_ONNX) / (1024 * 1024)
    print(f"[✓] Raw size: {raw_size:.2f} MB -> Quantized INT8 size: {quant_size:.2f} MB")
    
    shutil.copyfile(QUANT_ONNX, DEST_EXT)
    print(f"[✓] Copied to extension: {DEST_EXT}")

if __name__ == '__main__':
    process()
