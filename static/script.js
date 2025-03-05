
        document.addEventListener('DOMContentLoaded', function() {
            // Tab switching functionality
            const tabs = document.querySelectorAll('.tab');
            const tabContents = document.querySelectorAll('.tab-content');
            
            tabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    const tabId = tab.getAttribute('data-tab');
                    
                    // Remove active class from all tabs and contents
                    tabs.forEach(t => t.classList.remove('active'));
                    tabContents.forEach(c => c.classList.remove('active'));
                    
                    // Add active class to clicked tab and corresponding content
                    tab.classList.add('active');
                    document.getElementById(`${tabId}-tab`).classList.add('active');
                });
            });
            
            // Load models dynamically
            fetch('/models')
                .then(response => response.json())
                .then(models => {
                    const modelSelect = document.getElementById('model');
                    modelSelect.innerHTML = '';
                    
                    models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model.id;
                        option.textContent = model.name;
                        modelSelect.appendChild(option);
                    });
                })
                .catch(error => {
                    console.error('Error loading models:', error);
                });
            
            // Generate form submission
            const generateForm = document.getElementById('generate-form');
            const loader = document.querySelector('.loader');
            const resultContainer = document.getElementById('result-container');
            const generatedImage = document.getElementById('generated-image');
            const imageOverlay = document.getElementById('image-overlay');
            const successMessage = document.getElementById('success-message');
            const errorMessage = document.getElementById('error-message');
            const errorText = document.getElementById('error-text');
            
            generateForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                // Show loader and hide result
                loader.style.display = 'block';
                resultContainer.style.display = 'none';
                successMessage.style.display = 'none';
                errorMessage.style.display = 'none';
                
                // Get form data
                const formData = new FormData(generateForm);
                
                // Send request to server
                fetch('/generate', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    // Hide loader
                    loader.style.display = 'none';
                    
                    if (data.error) {
                        // Show error message
                        errorText.textContent = data.error;
                        errorMessage.style.display = 'block';
                        return;
                    }
                    
                    // Show result
                    generatedImage.src = 'data:image/png;base64,' + data.image;
                    resultContainer.style.display = 'block';
                    
                    // Show or hide secret message indicator
                    imageOverlay.style.display = data.hasSecret ? 'flex' : 'none';
                    
                    // Show success message if a secret was embedded
                    if (data.hasSecret) {
                        successMessage.style.display = 'block';
                    }
                })
                .catch(error => {
                    // Hide loader and show error
                    loader.style.display = 'none';
                    errorText.textContent = 'An error occurred. Please try again.';
                    errorMessage.style.display = 'block';
                    console.error('Error:', error);
                });
            });
            
            // Download button functionality
            const downloadBtn = document.getElementById('download-btn');
            downloadBtn.addEventListener('click', function() {
                const imageUrl = generatedImage.src;
                const link = document.createElement('a');
                link.href = imageUrl;
                link.download = 'steganai_' + Date.now() + '.png';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            });
            
            // Share button functionality
            const shareBtn = document.getElementById('share-btn');
            shareBtn.addEventListener('click', function() {
                if (navigator.share) {
                    // Convert base64 to blob
                    fetch(generatedImage.src)
                        .then(res => res.blob())
                        .then(blob => {
                            const file = new File([blob], 'steganai.png', { type: 'image/png' });
                            navigator.share({
                                title: 'SteganoAI - Hidden Message',
                                text: 'I created this image with a hidden message using SteganoAI!',
                                files: [file]
                            })
                            .catch(error => {
                                console.error('Error sharing:', error);
                                alert('Could not share the image. Try downloading it instead.');
                            });
                        });
                } else {
                    alert('Web Share API is not supported in your browser. Try downloading the image instead.');
                }
            });
            
            // Drag and drop functionality
            const dropArea = document.getElementById('drop-area');
            const fileInput = document.getElementById('file-input');
            const browseBtn = document.getElementById('browse-btn');
            const selectedImageContainer = document.getElementById('selected-image-container');
            const selectedImage = document.getElementById('selected-image');
            const decryptForm = document.getElementById('decrypt-form');
            
            // Open file explorer when browse button is clicked
            browseBtn.addEventListener('click', () => {
                fileInput.click();
            });
            
            // Handle file selection
            fileInput.addEventListener('change', function() {
                handleFile(this.files[0]);
            });
            
            // Highlight drop area when file is dragged over
            ['dragenter', 'dragover'].forEach(eventName => {
                dropArea.addEventListener(eventName, function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    dropArea.classList.add('active');
                }, false);
            });
            
            // Remove highlight when file is no longer over drop area
            ['dragleave', 'drop'].forEach(eventName => {
                dropArea.addEventListener(eventName, function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    dropArea.classList.remove('active');
                }, false);
            });
            
            // Handle dropped file
            dropArea.addEventListener('drop', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                if (e.dataTransfer.files.length) {
                    handleFile(e.dataTransfer.files[0]);
                }
            }, false);
            
            // Process the selected file
            function handleFile(file) {
                // Check if file is an image
                if (!file.type.match('image.*')) {
                    alert('Please select an image file.');
                    return;
                }
                
                // Display the selected image
                const reader = new FileReader();
                reader.onload = function(e) {
                    selectedImage.src = e.target.result;
                    selectedImageContainer.style.display = 'block';
                    decryptForm.style.display = 'block';
                };
                reader.readAsDataURL(file);
                
                // Store the file for later submission
                decryptForm.file = file;
            }
            
            // Decrypt form submission
            const decryptLoader = document.getElementById('decrypt-loader');
            const decryptedMessage = document.getElementById('decrypted-message');
            const messageContent = document.getElementById('message-content');
            const decryptError = document.getElementById('decrypt-error');
            const decryptErrorText = document.getElementById('decrypt-error-text');
            
            decryptForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                if (!decryptForm.file) {
                    alert('Please select an image first.');
                    return;
                }
                
                // Show loader and hide result
                decryptLoader.style.display = 'block';
                decryptedMessage.style.display = 'none';
                decryptError.style.display = 'none';
                
                // Create form data
                const formData = new FormData();
                formData.append('image', decryptForm.file);
                formData.append('password', document.getElementById('decrypt-password').value);
                
                // Send request to server
                fetch('/decrypt', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    // Hide loader
                    decryptLoader.style.display = 'none';
                    
                    if (data.error) {
                        // Show error message
                        decryptErrorText.textContent = data.error;
                        decryptError.style.display = 'block';
                        return;
                    }
                    
                    // Show decrypted message
                    messageContent.textContent = data.message;
                    decryptedMessage.style.display = 'block';
                })
                .catch(error => {
                    // Hide loader and show error
                    decryptLoader.style.display = 'none';
                    decryptErrorText.textContent = 'An error occurred. Please try again.';
                    decryptError.style.display = 'block';
                    console.error('Error:', error);
                });
            });
            
            // Initialize UI elements
            document.getElementById('decrypt-loader').style.display = 'none';
        });