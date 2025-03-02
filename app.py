import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import io
import logging
from pathlib import Path
from deep_translator import GoogleTranslator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisionSpeakApp:
    def __init__(self):
        # User inputs API key manually
        self.api_key = st.text_input("Enter your OpenAI API Key:", type="password")
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None  # No API key entered yet
        
        # Define supported languages and voices
        self.LANGUAGES = {
            "English": "en",
            "Telugu": "te",
            "Tamil": "ta",
            "Kannada": "kn",
            "Hindi": "hi"
        }
        
        self.NATIVE_NAMES = {
            "English": "English",
            "Telugu": "తెలుగు",
            "Tamil": "தமிழ்",
            "Kannada": "ಕನ್ನಡ",
            "Hindi": "हिंदी"
        }
        
        self.VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        
        # Create directory for audio files if it doesn't exist
        self.audio_dir = Path("audio_files")
        self.audio_dir.mkdir(exist_ok=True)

    def translate_text(self, text: str, target_language: str) -> str:
        """Translate text to the target language."""
        if target_language == "en":
            return text
        try:
            return GoogleTranslator(source="auto", target=target_language).translate(text)
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text  # Fallback to original text

    def image_to_data_url(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 data URL."""
        try:
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG", quality=85)
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            return f"data:image/jpeg;base64,{img_base64}"
        except Exception as e:
            logger.error(f"Error converting image: {e}")
            return ""

    def generate_audio(self, text: str, language: str = "en", voice: str = "alloy") -> str:
        """Generate audio from text using OpenAI's TTS model."""
        if not self.client:
            st.error("API key is missing. Please enter a valid OpenAI API key.")
            return ""

        try:
            translated_text = self.translate_text(text, language)
            audio_file_path = self.audio_dir / f"description_{language}_{voice}.mp3"

            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=translated_text
            )

            response.stream_to_file(str(audio_file_path))
            return str(audio_file_path)
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            return ""

    def get_image_description(self, image_data_url: str) -> str:
        """Get a detailed image description using OpenAI GPT-4 Vision."""
        if not self.client:
            st.error("API key is missing. Please enter a valid OpenAI API key.")
            return ""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Describe this image in detail for a visually impaired user."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this image in detail."},
                            {"type": "image_url", "image_url": {"url": image_data_url}}
                        ]
                    }
                ],
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error getting image description: {e}")
            return "Failed to generate description."

    def run(self):
        """Run the Streamlit application."""
        st.title("VisionSpeak: Image Description for the Visually Impaired")

        st.markdown("""
        **How to use:**
        1. Enter your OpenAI API Key.
        2. Select your preferred language and voice.
        3. Capture an image using your camera.
        4. Get a detailed description and audio feedback.
        """)

        if not self.api_key:
            st.warning("Please enter your OpenAI API key to proceed.")
            return  # Stop execution until API key is provided

        # Language and voice selection
        col1, col2 = st.columns(2)
        with col1:
            audio_language = st.selectbox(
                "Select Audio Language",
                options=list(self.LANGUAGES.keys()),
                format_func=lambda x: f"{x} ({self.NATIVE_NAMES[x]})",
                index=0
            )
        with col2:
            voice = st.selectbox("Select Voice", options=self.VOICES, index=0)

        # Capture image
        captured_image = st.camera_input("Take a picture")

        if captured_image:
            with st.spinner("Processing image..."):
                image = Image.open(captured_image)
                image_data_url = self.image_to_data_url(image)
                
                if not image_data_url:
                    st.error("Error processing image.")
                    return

                description = self.get_image_description(image_data_url)

                if description:
                    st.subheader("Description")
                    st.write(description)

                    if audio_language != "English":
                        translated_description = self.translate_text(description, self.LANGUAGES[audio_language])
                        st.subheader(f"Description in {audio_language}")
                        st.write(translated_description)

                    # Generate and play audio
                    st.subheader("Audio Description")
                    with st.spinner("Generating audio..."):
                        audio_file = self.generate_audio(description, self.LANGUAGES[audio_language], voice)
                        if audio_file:
                            st.audio(audio_file, format="audio/mp3")

if __name__ == "__main__":
    app = VisionSpeakApp()
    app.run()
