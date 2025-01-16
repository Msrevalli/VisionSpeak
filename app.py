import streamlit as st
from openai import OpenAI
import cv2  # Import OpenCV for capturing images
import numpy as np  # Import numpy for image processing
import base64  # Import base64 for encoding the image

import os
os.environ["OPENAI_API_KEY"] = st.secrets['OPENAI_API_KEY']

# Title of the app
st.title("Webcam Image Capture")

# Function to capture an image from the webcam
def capture_image():
    # Open the webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("Error: Could not open webcam.")
        return None

    # Capture a frame
    ret, frame = cap.read()

    if not ret:
        st.error("Error: Failed to capture image.")
        return None

    # Release the webcam
    cap.release()

    # Convert the frame from BGR (OpenCV) to RGB (PIL)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return frame_rgb

# Function to convert image to base64 data URL
def image_to_data_url(image):
    _, buffer = cv2.imencode('.jpg', image)  # Encode the image as JPEG
    img_base64 = base64.b64encode(buffer).decode('utf-8')  # Convert to base64
    return f"data:image/jpeg;base64,{img_base64}"  # Create data URL

# Main app logic
def main():
    # Add a button to capture an image
    if st.button("Capture Image"):
        # Capture the image
        image = capture_image()

        if image is not None:
            # Display the captured image
            st.image(image, caption="Captured Image", use_container_width=True)

            client = OpenAI()  # Initialize the OpenAI client

            # Convert the captured image to a data URL
            image_data_url = image_to_data_url(image)

            # Ensure the image is passed correctly
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",  # Added system message
                        "content": "You are an assistant that explains image contents."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What is happening in this image?"},
                            {
                                "type": "image_url",  # Use image_url
                                "image_url": {
                                    "url": image_data_url,  # Use the data URL of the captured image
                                },
                            },
                        ],
                    }
                ],
                max_tokens=1000,
            )

            # Display the response content in the app
            st.write(response.choices[0].message.content)

# Run the app
if __name__ == "__main__":
    main()