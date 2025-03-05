from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import os
import io
import base64
from PIL import Image
from dotenv import load_dotenv
import numpy as np
import random
import hashlib

# Load environment variables
load_dotenv()
app = Flask(__name__)

# Get API key from environment variable
API_TOKEN = os.environ.get("API_TOKEN")

# Hugging Face Inference API URL
API_URL = "https://api-inference.huggingface.co/models/"

# Default model
DEFAULT_MODEL = "stabilityai/stable-diffusion-3.5-large"

class Steganography:
    @staticmethod
    def string_to_binary(message):
        """Convert string to binary"""
        binary = ''.join(format(ord(char), '08b') for char in message)
        return binary
    
    @staticmethod
    def binary_to_string(binary):
        """Convert binary to string"""
        # Ensure the binary string length is a multiple of 8
        binary = binary + '0' * (8 - len(binary) % 8) if len(binary) % 8 != 0 else binary
        
        string = ''
        for i in range(0, len(binary), 8):
            byte = binary[i:i+8]
            string += chr(int(byte, 2))
        return string.rstrip('\x00')  # Remove null terminators
    
    @staticmethod
    def encrypt_message(image, message, password=None):
        """Embed a message in an image using LSB steganography with optional password"""
        # Convert the image to RGB if it's not already
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Get the pixels as a numpy array
        pixels = np.array(image)
        
        # Flatten the pixel array for easier manipulation
        flat_pixels = pixels.reshape(-1)
        
        # If password is provided, use it to generate a seed for pixel selection
        if password:
            seed = int(hashlib.sha256(password.encode('utf-8')).hexdigest(), 16) % 10**8
            random.seed(seed)
            pixel_indices = random.sample(range(len(flat_pixels)), len(flat_pixels))
        else:
            pixel_indices = range(len(flat_pixels))
        
        # Convert message to binary
        binary_message = Steganography.string_to_binary(message)
        
        # Add message length at the beginning (32 bits) for easier extraction
        message_length_binary = format(len(binary_message), '032b')
        binary_data = message_length_binary + binary_message
        
        # Check if the image can hold the message
        if len(binary_data) > len(flat_pixels):
            raise ValueError("Message too long for this image")
        
        # Create a copy of the flattened pixels to avoid modifying the original array
        modified_pixels = flat_pixels.copy()
        
        # Embed the binary data into the image
        for i, bit in enumerate(binary_data):
            if i >= len(modified_pixels):
                break
            
            # Get the next pixel index based on our selection method
            if password:
                idx = pixel_indices[i]
            else:
                idx = i
            
            # Modify the least significant bit - fixed to work with uint8
            if int(bit) == 1:
                modified_pixels[idx] = modified_pixels[idx] | 1  # Set LSB to 1
            else:
                modified_pixels[idx] = modified_pixels[idx] & 254  # Set LSB to 0 (254 is binary 11111110)
        
        # Reshape back to original image dimensions
        modified_pixels = modified_pixels.reshape(pixels.shape)
        
        # Create a new image with the modified pixels
        stego_image = Image.fromarray(modified_pixels.astype('uint8'))
        return stego_image
    
    @staticmethod
    def decrypt_message(image, password=None):
        """Extract a message from an image using LSB steganography with optional password"""
        # Convert the image to RGB if it's not already
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Get the pixels as a numpy array
        pixels = np.array(image)
        
        # Flatten the pixel array for easier manipulation
        flat_pixels = pixels.reshape(-1)
        
        # If password is provided, use it to generate a seed for pixel selection
        if password:
            seed = int(hashlib.sha256(password.encode('utf-8')).hexdigest(), 16) % 10**8
            random.seed(seed)
            pixel_indices = random.sample(range(len(flat_pixels)), len(flat_pixels))
        else:
            pixel_indices = range(len(flat_pixels))
        
        # Extract binary data
        binary_data = ''
        
        # First get the message length (first 32 bits)
        for i in range(32):
            if password:
                idx = pixel_indices[i]
            else:
                idx = i
                
            binary_data += str(flat_pixels[idx] & 1)
        
        # Convert the first 32 bits to get the message length
        message_length = int(binary_data, 2)
        
        # Extract the actual message bits
        binary_message = ''
        for i in range(32, 32 + message_length):
            if i >= len(flat_pixels):
                break
                
            if password:
                idx = pixel_indices[i]
            else:
                idx = i
                
            binary_message += str(flat_pixels[idx] & 1)
        
        # Convert binary message to string
        message = Steganography.binary_to_string(binary_message)
        return message

@app.route('/', methods=['GET'])
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_image():
    """Generate an image based on the prompt and embed a secret message."""
    if not API_TOKEN:
        return jsonify({"error": "API key not configured. Please set the API_TOKEN environment variable."}), 500
    
    # Get form data
    prompt = request.form.get('prompt', '')
    model = request.form.get('model', DEFAULT_MODEL)
    secret_message = request.form.get('secret_message', '')
    password = request.form.get('password', '')
    
    if not prompt:
        return jsonify({"error": "Please enter a prompt"}), 400
    
    try:
        # Set up the headers with API key
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        
        # Prepare the payload - text-to-image requires a JSON payload
        payload = {
            "inputs": prompt,
        }
        
        # Send request to Hugging Face - note we're appending the model to the URL
        model_api_url = f"{API_URL}{model}"
        response = requests.post(model_api_url, headers=headers, json=payload)
        
        # Check if the request was successful
        if response.status_code != 200:
            error_msg = f"API Error: {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg = f"API Error: {error_data['error']}"
            except:
                pass
            return jsonify({"error": error_msg}), 500
        
        # Get the image data
        image_bytes = response.content
        
        # Open the image using PIL
        image = Image.open(io.BytesIO(image_bytes))
        
        # Embed the secret message if provided
        if secret_message:
            try:
                stego_image = Steganography.encrypt_message(image, secret_message, password)
                
                # Save the stego image to bytes
                output_buffer = io.BytesIO()
                stego_image.save(output_buffer, format="PNG")
                image_bytes = output_buffer.getvalue()
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
        
        # Convert to base64 for HTML display
        img_str = base64.b64encode(image_bytes).decode('utf-8')
        
        return jsonify({
            "image": img_str,
            "prompt": prompt,
            "model": model,
            "hasSecret": bool(secret_message)
        })
    
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        return jsonify({"error": f"Failed to generate image: {str(e)}"}), 500

@app.route('/decrypt', methods=['POST'])
def decrypt_image():
    """Decrypt a message from an uploaded image."""
    try:
        # Get the uploaded image
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
            
        image_file = request.files['image']
        password = request.form.get('password', '')
        
        # Open the image using PIL
        image = Image.open(image_file)
        
        # Extract the message
        message = Steganography.decrypt_message(image, password)
        
        return jsonify({"message": message})
    
    except Exception as e:
        print(f"Error decrypting image: {str(e)}")
        return jsonify({"error": f"Failed to decrypt image: {str(e)}"}), 500

@app.route('/models', methods=['GET'])
def get_models():
    """Return a list of available models."""
    # List of recommended Stable Diffusion models
    models = [
        {"id": "stabilityai/stable-diffusion-3.5-large", "name": "Stable Diffusion 3.5 Large"},
        {"id": "stabilityai/stable-diffusion-3.0-base", "name": "Stable Diffusion 3.0 Base"},
        {"id": "stabilityai/stable-diffusion-2-1", "name": "Stable Diffusion 2.1"},
        {"id": "runwayml/stable-diffusion-v1-5", "name": "Stable Diffusion 1.5"},
    ]
    return jsonify(models)

if __name__ == '__main__':
    print(f"API Key configured: {'Yes' if API_TOKEN else 'No - please set API_TOKEN in .env file'}")
    print("Starting Flask server. Access the app at http://127.0.0.1:5000/")
    app.run(debug=True)





