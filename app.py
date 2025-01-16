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

# Function to generate audio from text using OpenAI's TTS model
def generate_audio(text, language="en", voice="alloy"):
    client = OpenAI()
    try:
        # Use OpenAI's TTS model to generate audio
        response = client.audio.speech.create(
            model="tts-1",  # Use the TTS model
            voice=voice,  # Choose a voice (alloy, echo, fable, onyx, nova, shimmer)
            input=text+"in"+language,
        )
        # Save the audio to a temporary file
        audio_file = f"description_{language}.mp3"
        response.stream_to_file(audio_file)
        return audio_file
    except Exception as e:
        st.error(f"Error generating audio: {e}")
        return None

# Main app logic
def main():
    # Add a language selection dropdown for audio
    audio_language = st.selectbox(
        "Select Audio Language",
        options=["English", "Telugu", "Tamil", "Kannada", "Hindi"],
        index=0,
    )

    # Map language selection to language codes
    language_map = {
        "English": "en",
        "Telugu": "te",
        "Tamil": "ta",
        "Kannada": "kn",
        "Hindi": "hi",
    }
    audio_language_code = language_map[audio_language]

    # Add a voice selection dropdown for audio
    voice = st.selectbox(
        "Select Voice",
        options=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        index=0,
    )

    # Use Streamlit's camera input to capture an image
    st.write("Capture an image using your selected camera, and VisionSpeak will describe it for you.")
    captured_image = st.camera_input("Take a picture")

    # If an image is captured
    if captured_image is not None:
        # Convert the image to a PIL Image object
        image = Image.open(captured_image)

        # Convert the image to a base64 data URL
        image_data_url = image_to_data_url(image)

        # Initialize the OpenAI client
        client = OpenAI()

        # Send the image to OpenAI GPT-4 for description (in English)
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # Use the latest GPT-4 model
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are an assistant that describes images in detail for visually impaired users. 
                    Your descriptions should be clear, concise, and focus on the most important elements of the image. 
                    Include details about objects, people, actions, colors, and the overall scene. 
                    If the image contains text, read it aloud. 
                    Provide context and explanations where necessary.
                    Respond in English.
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

        # Get the description from the response
        description = response.choices[0].message.content

        # Display the response content in the app
        st.write("**Description:**")
        st.write(description)

        # Generate audio from the description in the selected language
        st.write("**Audio Description:**")
        audio_file = generate_audio(description, audio_language_code, voice)

        # Play the audio in the app
        if audio_file:
            st.audio(audio_file, format="audio/mp3")

# Run the app
if __name__ == "__main__":
    main()
