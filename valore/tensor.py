from keras.models import load_model  # TensorFlow is required for Keras to work
from PIL import ImageOps  # Pillowを使用
import tensorflow as tf
import numpy as np
import cv2, math
from typing import List


def trimVideo(targetFilename, targetMillis, top, bottom, left, right):
    #動画のFPS、フレーム数・幅高さ取得
    videoCapture = cv2.VideoCapture(targetFilename)
    fps = videoCapture.get(cv2.CAP_PROP_FPS)
    width = int(videoCapture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(videoCapture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    #トリミング範囲のチェック
    if left < 0 or right > width or top < 0 or bottom > height:
        print("エラー:トリミング範囲が動画の範囲外です。")
        print(f"width = {width}, height = {height}")
        return

    targetFrameIndex = math.ceil(fps * targetMillis / 1000)

    #指定フレームに移動
    videoCapture.set(cv2.CAP_PROP_POS_FRAMES, targetFrameIndex)
    ret, img = videoCapture.read()
    if not ret:
        print("failed to read the frame")
        return
    
    #画像をトリミング
    cropped_img = img[top:bottom, left:right]

    croppedarray = np.array(cropped_img)

    # Disable scientific notation for clarity
    np.set_printoptions(suppress=True)

    # Load the model
    model = load_model(r"C:\Users\daiki\AppData\Local\Programs\Python\Python311\valore\converted_keras\keras_model.h5", compile=False)
    
    # Load the labels
    class_names = open(r"C:\Users\daiki\AppData\Local\Programs\Python\Python311\valore\converted_keras\labels.txt", "r").readlines()

    # Check if the input is a NumPy array
    if isinstance(croppedarray, np.ndarray):
        # Resize the image to (224, 224) using OpenCV
        image = cv2.resize(croppedarray, (224, 224))
        # Normalize the image to (-1, 1)
        normalized_image_array = (image.astype(np.float32) / 127.5) - 1
    else:
        raise ValueError("Expected a NumPy array for `croppedarray`")

    # Create the array of the right shape to feed into the keras model
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    data[0] = normalized_image_array

    # Predicts the model
    prediction = model.predict(data)
    index = np.argmax(prediction)
    class_name = class_names[index]
    confidence_score = prediction[0][index]

    # Print prediction and confidence score
    print(f"analyzed at sec_{int(targetMillis / 1000)}")
    print("Class:", class_name[2:], end="")
    print("Confidence Score:", confidence_score)
    return index    