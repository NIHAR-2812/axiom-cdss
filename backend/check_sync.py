import tensorflow as tf
import os

# Path to your optimized model
model_path = os.path.join("..", "ml_engine", "models", "cdss_model_quantized.tflite")

interpreter = tf.lite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

output_details = interpreter.get_output_details()
# Assuming output index 0 is disease, index 1 is medication
disease_output_shape = output_details[0]['shape']

print(f"Model's Disease Output Layer Shape: {disease_output_shape}")
print(f"Total Output Neurons (Classes): {disease_output_shape[1]}")