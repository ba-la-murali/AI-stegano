from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import os
import io
import base64
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get API key from environment variable
API_TOKEN = os.environ.get("API_TOKEN")

# Hugging Face Inference API URL
API_URL = "https://api-inference.huggingface.co/models/"

# Default model
DEFAULT_MODEL = "stabilityai/stable-diffusion-3.5-large"

@app.route('/', methods=['GET'])
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_image():
    """Generate an image based on the prompt."""
    if not API_TOKEN:
        return jsonify({"error": "API key not configured. Please set the API_TOKEN environment variable."}), 500
    
    # Get form data
    prompt = request.form.get('prompt', '')
    model = request.form.get('model', DEFAULT_MODEL)
    
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
        
        # Get the image bytes
        image_bytes = response.content
        
        # Convert to base64 for HTML display
        img_str = base64.b64encode(image_bytes).decode('utf-8')
        
        return jsonify({
            "image": img_str,
            "prompt": prompt,
            "model": model
        })
    
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        return jsonify({"error": f"Failed to generate image: {str(e)}"}), 500

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