import os
import requests
import time
from datetime import datetime

#  creating a  file where your  api-key & source image url will be store for future events
CONFIG_FILE = 'config.txt'

# Loading configuration from file
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, 'r') as file:
        lines = file.readlines()
        config = {}
        for line in lines:
            key, value = line.strip().split('=', 1)
            config[key] = value
        return config

# Saving configuration to file
def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        for key, value in config.items():
            file.write(f"{key}={value}\n")

# genreating unique file name so old file can't be overwrited
def generate_unique_filename():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"swapped_image_{timestamp}.jpg"

# Detecting faces function
def detect_faces(api_key, image_url):
    try:
        headers = {'x-api-key': api_key, 'Content-Type': 'application/json'}
        response = requests.post(
            'https://api.maxstudio.ai/detect-face-image',
            headers=headers,
            json={'imageUrl': image_url}
        )
        faces_data = response.json()
        print("Response from face detection:", faces_data)
        return faces_data.get('detectedFaces', [])
    except Exception as error:
        print('Error during face detection:', str(error))
        raise

# Main face swap process
def face_swap(api_key, source_image_url, target_image_url):
    # Detect faces in the target image
    faces = detect_faces(api_key, target_image_url)
    print("Detected faces:", faces)

    if not faces:
        print("No faces detected in the target image.")
        return

    # Prepare face swap payload
    faces_payload = [
        {
            'newFace': source_image_url,
            'originalFace': {
                'x': face['x'],
                'y': face['y'],
                'width': face['width'],
                'height': face['height']
            }
        } for face in faces
    ]

    swap_payload = {
        'mediaUrl': target_image_url,
        'faces': faces_payload
    }

    # Initiating face swap request
    headers = {'x-api-key': api_key, 'Content-Type': 'application/json'}
    try:
        print("Swap Payload:", swap_payload)
        swap_response = requests.post('https://api.maxstudio.ai/swap-image', headers=headers, json=swap_payload)

        print("Swap Response Status Code:", swap_response.status_code)
        print("Swap Response Content:", swap_response.text)

        swap_data = swap_response.json()
        job_id = swap_data.get('jobId')

        if job_id:
            # Monitor job status
            while True:
                status_response = requests.get(f'https://api.maxstudio.ai/swap-image/{job_id}', headers=headers)
                status_data = status_response.json()

                print("Job Status Response:", status_data)

                if status_data.get('status') == 'completed':
                    result_url = status_data.get('result', {}).get('mediaUrl')
                    if result_url:
                        print("Result URL:", result_url)
                        # Downloading the result image
                        result_image = requests.get(result_url).content
                        unique_filename = generate_unique_filename()
                        with open(unique_filename, 'wb') as file:
                            file.write(result_image)
                        print(f"Face swap completed. Image saved as '{unique_filename}'.")
                    else:
                        print("No result URL found in the response.")
                    break
                elif status_data.get('status') == 'failed':
                    print("Face swap failed.")
                    break
                else:
                    print("Processing... Checking again in 5 seconds.")
                    time.sleep(5)
        else:
            print("Failed to initiate face swap. No jobId returned.")
    except Exception as error:
        print('Error during face swap:', str(error))

# Main script
if __name__ == "__main__":
    # Load config
    config = load_config()

    # Prompt for missing values
    if 'API_KEY' not in config:
        config['API_KEY'] = input("Enter your API key: ").strip()
    if 'SOURCE_IMAGE_URL' not in config:
        config['SOURCE_IMAGE_URL'] = input("Enter the source image URL: ").strip()

    # Save config
    save_config(config)

    # Input target image URL for face swapping
    target_image_url = input("Enter the target image URL: ").strip()

    # Execute face swap
    face_swap(config['API_KEY'], config['SOURCE_IMAGE_URL'], target_image_url)
