import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import io
import os

# Set OpenAI API key from Streamlit secrets
os.environ["OPENAI_API_KEY"] = st.secrets['OPENAI_API_KEY']

# Title of the app
st.title("VisionSpeak: Image Description for the Visually Impaired")

# Function to convert image to base64 data URL
def image_to_data_url(image):
    buffered = io.BytesIO()  # Create a buffer to hold the image data
    image.save(buffered, format="JPEG")  # Save the image as JPEG to the buffer
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')  # Convert to base64
    return f"data:image/jpeg;base64,{img_base64}"  # Create data URL

# Main app logic
def main():
    # Use Streamlit's camera input to capture an image
    st.write("Capture an image using your camera, and VisionSpeak will describe it for you.")
    captured_image = st.camera_input("Take a picture")

    # If an image is captured
    if captured_image is not None:
        # Convert the image to a PIL Image object
        image = Image.open(captured_image)

        # Display the captured image (optional, for sighted users or debugging)
        st.image(image, caption="Captured Image", use_column_width=True)

        # Convert the image to a base64 data URL
        image_data_url = image_to_data_url(image)

        # Initialize the OpenAI client
        client = OpenAI()

        # Send the image to OpenAI GPT-4 for description
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",  # Use GPT-4 Vision model
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are an assistant that describes images in detail for visually impaired users. 
                    Your descriptions should be clear, concise, and focus on the most important elements of the image. 
                    Include details about objects, people, actions, colors, and the overall scene. 
                    If the image contains text, read it aloud. 
                    Provide context and explanations where necessary.
                    """
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Please describe this image in detail for a visually impaired user."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data_url,  # Use the data URL of the captured image
                            },
                        },
                    ],
                }
            ],
            max_tokens=1000,  # Limit the response length
        )

        # Display the response content in the app
        st.write("**Description:**")
        st.write(response.choices[0].message.content)

# Run the app
if __name__ == "__main__":
    main()
