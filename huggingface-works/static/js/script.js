document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const form = document.getElementById('generation-form');
    const promptInput = document.getElementById('prompt');
    const modelSelect = document.getElementById('model');
    const generateBtn = document.getElementById('generate-btn');
    const clearBtn = document.getElementById('clear-btn');
    const downloadBtn = document.getElementById('download-btn');
    const resultContainer = document.getElementById('result-container');
    const resultImage = document.getElementById('result-image');
    const resultPrompt = document.getElementById('result-prompt');
    const resultModel = document.getElementById('result-model');
    const loadingElement = document.getElementById('loading');
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');

    // Load available models
    fetch('/models')
        .then(response => response.json())
        .then(models => {
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.name;
                modelSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading models:', error);
            showError('Failed to load available models.');
        });

    // Handle form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        generateImage();
    });

    // Handle clear button
    clearBtn.addEventListener('click', function() {
        promptInput.value = '';
        hideError();
        resultContainer.style.display = 'none';
    });

    // Handle download button
    downloadBtn.addEventListener('click', function() {
        if (resultImage.src) {
            const link = document.createElement('a');
            link.href = resultImage.src;
            link.download = 'generated-image.png';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    });

    // Function to generate image
    function generateImage() {
        const prompt = promptInput.value.trim();
        const model = modelSelect.value;

        if (!prompt) {
            showError('Please enter a prompt.');
            return;
        }

        // Show loading indicator
        showLoading();
        hideError();
        resultContainer.style.display = 'none';

        // Create form data
        const formData = new FormData();
        formData.append('prompt', prompt);
        formData.append('model', model);

        // Send request to server
        fetch('/generate', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Failed to generate image');
                });
            }
            return response.json();
        })
        .then(data => {
            // Display the generated image
            resultImage.src = 'data:image/png;base64,' + data.image;
            resultPrompt.textContent = data.prompt;
            resultModel.textContent = data.model;
            resultContainer.style.display = 'block';
            hideLoading();
        })
        .catch(error => {
            console.error('Error:', error);
            showError(error.message);
            hideLoading();
        });
    }

    // Helper functions
    function showLoading() {
        loadingElement.style.display = 'flex';
        generateBtn.disabled = true;
    }

    function hideLoading() {
        loadingElement.style.display = 'none';
        generateBtn.disabled = false;
    }

    function showError(message) {
        errorText.textContent = message;
        errorMessage.style.display = 'flex';
    }

    function hideError() {
        errorMessage.style.display = 'none';
    }
});