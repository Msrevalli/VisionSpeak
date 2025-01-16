import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import io
import os
from typing import Optional
import logging
from pathlib import Path
from translate import Translator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisionSpeakApp:
    def __init__(self):
        # Set OpenAI API key from Streamlit secrets
        self.api_key = self._set_api_key()
        self.client = OpenAI()
        
        # Define supported languages and voices
        self.LANGUAGES = {
            "English": "en",
            "Telugu": "te",
            "Tamil": "ta",
            "Kannada": "kn",
            "Hindi": "hi"
        }
        
        # Language names in their native script
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

    @staticmethod
    def _set_api_key() -> str:
        """Set up OpenAI API key from Streamlit secrets."""
        try:
            api_key = st.secrets['OPENAI_API_KEY']
            os.environ["OPENAI_API_KEY"] = api_key
            return api_key
        except KeyError:
            st.error("OpenAI API key not found in Streamlit secrets.")
            return ""

    def translate_text(self, text: str, target_language: str) -> str:
        """Translate text to target language."""
        try:
            if target_language == "en":
                return text
            
            # Initialize translator for target language
            translator = Translator(to_lang=target_language)
            
            # Split text into smaller chunks (translator has a length limit)
            chunks = [text[i:i+500] for i in range(0, len(text), 500)]
            
            # Translate each chunk and combine
            translated_chunks = [translator.translate(chunk) for chunk in chunks]
            translated_text = ' '.join(translated_chunks)
            
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            st.warning(f"Translation failed. Falling back to English. Error: {str(e)}")
            return text

    def image_to_data_url(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 data URL."""
        try:
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG", quality=85)
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            return f"data:image/jpeg;base64,{img_base64}"
        except Exception as e:
            logger.error(f"Error converting image to data URL: {e}")
            raise

    def generate_audio(self, text: str, language: str = "en", voice: str = "alloy") -> Optional[str]:
        """Generate audio from text using OpenAI's TTS model."""
        try:
            # Translate text to target language
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
            st.error(f"Failed to generate audio: {str(e)}")
            return None

    def get_image_description(self, image_data_url: str) -> str:
        """Get image description from OpenAI GPT-4 Vision."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """
                        You are an assistant that describes images in detail for visually impaired users. 
                        Your descriptions should be clear, concise, and focus on the most important elements of the image. 
                        Include details about:
                        - Objects and their spatial relationships
                        - People and their actions/expressions
                        - Colors and lighting
                        - Text content if present
                        - Overall scene context and mood
                        Use clear, specific language and avoid ambiguous terms.
                        """
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Please describe this image in detail for a visually impaired user."},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_data_url}
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error getting image description: {e}")
            st.error("Failed to generate image description. Please try again.")
            return ""

    def run(self):
        """Run the Streamlit application."""
        st.title("VisionSpeak: Image Description for the Visually Impaired by Sreevalli")
        
        # Add app description and instructions
        st.markdown("""
        VisionSpeak helps visually impaired users understand images through detailed descriptions and audio feedback.
        
        **How to use:**
        1. Select your preferred language and voice for the audio description
        2. Take a picture using your camera
        3. Wait for the description and audio to generate
        """)

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
            voice = st.selectbox(
                "Select Voice",
                options=self.VOICES,
                index=0
            )

        # Camera input
        captured_image = st.camera_input(
            "Take a picture",
            help="Click to capture an image using your camera"
        )

        if captured_image:
            with st.spinner("Processing image..."):
                # Process image
                image = Image.open(captured_image)
                image_data_url = self.image_to_data_url(image)
                
                # Get description
                description = self.get_image_description(image_data_url)
                
                if description:
                    # Display description
                    st.subheader("Description")
                    st.write(description)
                    
                    # Display translated description if not English
                    if audio_language != "English":
                        translated_description = self.translate_text(
                            description,
                            self.LANGUAGES[audio_language]
                        )
                        st.subheader(f"Description in {audio_language}")
                        st.write(translated_description)
                    
                    # Generate and play audio
                    st.subheader("Audio Description")
                    with st.spinner("Generating audio..."):
                        audio_file = self.generate_audio(
                            description,
                            self.LANGUAGES[audio_language],
                            voice
                        )
                        if audio_file:
                            st.audio(audio_file, format="audio/mp3")

if __name__ == "__main__":
    app = VisionSpeakApp()
    app.run()
