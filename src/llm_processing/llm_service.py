import logging
from typing import List, Optional, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from huggingface_hub import login

from ..config.settings import DEFAULT_LLM_MODEL, FALLBACK_LLM_MODEL, HUGGINGFACE_TOKEN, CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-based text processing using open-source models"""
    
    def __init__(self, model_name: str = DEFAULT_LLM_MODEL):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the LLM model and tokenizer with fallback support"""
        models_to_try = [self.model_name]
        
        # Add fallback model if different from default
        if self.model_name != FALLBACK_LLM_MODEL:
            models_to_try.append(FALLBACK_LLM_MODEL)
        
        # Add simple fallback models
        models_to_try.extend([
            "gpt2",  # Very reliable fallback
            "distilgpt2"  # Even smaller fallback
        ])
        
        for model_name in models_to_try:
            try:
                logger.info(f"Attempting to load model: {model_name} on device: {self.device}")
                
                # Login to Hugging Face if token provided
                if HUGGINGFACE_TOKEN:
                    login(token=HUGGINGFACE_TOKEN)
                
                # Load tokenizer with trust_remote_code for some models
                try:
                    self.tokenizer = AutoTokenizer.from_pretrained(
                        model_name,
                        trust_remote_code=True
                    )
                except Exception as tokenizer_error:
                    logger.warning(f"Error loading tokenizer for {model_name}: {tokenizer_error}")
                    continue
                
                # Add padding token if it doesn't exist
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                
                # Load model with appropriate configuration for available hardware
                model_kwargs = {
                    "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
                    "device_map": "auto" if self.device == "cuda" else None,
                    "low_cpu_mem_usage": True,
                    "trust_remote_code": True
                }
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name, 
                    **model_kwargs
                )
                
                # Create text generation pipeline
                self.pipeline = pipeline(
                    "text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device_map="auto" if self.device == "cuda" else None,
                    do_sample=True,
                    temperature=0.1,
                    max_new_tokens=512,
                    pad_token_id=self.tokenizer.eos_token_id
                )
                
                logger.info(f"✅ Successfully loaded model: {model_name}")
                self.model_name = model_name  # Update to the model that actually worked
                return
                
            except Exception as e:
                logger.warning(f"Failed to load model {model_name}: {e}")
                continue
        
        # If all models failed, raise the last error
        raise RuntimeError(
            "Failed to load any LLM model. Please ensure you have the required dependencies installed:\n"
            "pip install sentencepiece protobuf\n"
            "Or run: ./install_dependencies.sh"
        )
    
    def generate_response(self, prompt: str, max_tokens: int = 512) -> str:
        """
        Generate response from the LLM
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        try:
            # Format prompt based on model type
            if "mistral" in self.model_name.lower():
                # Mistral format
                formatted_prompt = f"<s>[INST] {prompt} [/INST]"
            elif "gpt" in self.model_name.lower():
                # GPT format
                formatted_prompt = f"Human: {prompt}\nAssistant:"
            else:
                # Default format
                formatted_prompt = prompt
            
            # Generate response
            try:
                response = self.pipeline(
                    formatted_prompt,
                    max_new_tokens=max_tokens,
                    temperature=0.1,
                    do_sample=True,
                    return_full_text=False,
                    pad_token_id=self.tokenizer.eos_token_id
                )
                
                generated_text = response[0]["generated_text"].strip()
                return generated_text
                
            except Exception as pipeline_error:
                logger.warning(f"Pipeline error, trying simpler generation: {pipeline_error}")
                
                # Fallback to direct model generation
                inputs = self.tokenizer.encode(formatted_prompt, return_tensors="pt")
                with torch.no_grad():
                    outputs = self.model.generate(
                        inputs,
                        max_new_tokens=max_tokens,
                        temperature=0.1,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id
                    )
                
                # Decode response
                generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                # Remove the input prompt from response
                if formatted_prompt in generated_text:
                    generated_text = generated_text.replace(formatted_prompt, "").strip()
                
                return generated_text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return ""
    
    def clean_transcript_text(self, raw_text: str) -> str:
        """
        Clean and format raw transcript text
        
        Args:
            raw_text: Raw transcript text from transcription service
            
        Returns:
            Cleaned and formatted text
        """
        prompt = f"""You are an expert in text formatting and linguistics. The following text is a raw, machine-generated transcript of a podcast segment. It may lack proper capitalization, punctuation, and sentence structure. Your task is to process this text and transform it into a clean, readable, and well-formatted paragraph. Ensure that you correct capitalization, add appropriate punctuation (periods, commas, question marks), and structure the text for maximum readability. Do not alter the underlying words or meaning. Here is the raw text:

{raw_text}

Please provide only the cleaned text without any additional commentary."""
        
        return self.generate_response(prompt, max_tokens=len(raw_text.split()) + 100)
    
    def generate_segment_title(self, cleaned_text: str) -> str:
        """
        Generate a concise title for a transcript segment
        
        Args:
            cleaned_text: Cleaned transcript text
            
        Returns:
            Generated title (7-10 words)
        """
        prompt = f"""You are a skilled content editor. I will provide you with a segment of a podcast transcript. Based on the content of this segment, generate a concise and descriptive title, no more than 7-10 words long. The title should capture the main topic or idea being discussed. If you were to give a title to this segment, what would it be? Here is the segment:

{cleaned_text}

Please provide only the title without any additional text or quotation marks."""
        
        return self.generate_response(prompt, max_tokens=20)
    
    def extract_insights(self, text_chunk: str, categories: List[str]) -> Dict[str, List[str]]:
        """
        Extract insights from a text chunk
        
        Args:
            text_chunk: Chunk of transcript text
            categories: List of insight categories to extract
            
        Returns:
            Dictionary with categories as keys and lists of insights as values
        """
        categories_str = ", ".join(categories)
        
        prompt = f"""Please carefully read the following podcast transcript chunk. Your task is to extract all the key insights discussed. Organize these insights into the following categories: {categories_str}. For each insight, provide the verbatim quote or a detailed summary of the concept. Here is the transcript chunk:

{text_chunk}

Please format your response as follows:
Category 1:
- Insight 1
- Insight 2

Category 2:
- Insight 1
- Insight 2

Only include categories that have actual insights found in the text."""
        
        response = self.generate_response(prompt, max_tokens=800)
        return self._parse_insights_response(response, categories)
    
    def find_timestamp_for_insight(self, full_transcript: str, insight_text: str) -> tuple[Optional[float], Optional[float]]:
        """
        Find the timestamp for a specific insight in the full transcript
        
        Args:
            full_transcript: Full transcript with timestamps
            insight_text: Specific insight text to find
            
        Returns:
            Tuple of (start_time, end_time) or (None, None) if not found
        """
        prompt = f"""I will provide you with a full podcast transcript that includes timestamps, and a specific quote or insight that was extracted from it. Your task is to find the exact start and end time of when this specific quote or insight was said in the podcast. Analyze the transcript and return only the start and end times in seconds. Here is the transcript:

{full_transcript[:4000]}...  # Truncate for context window

And here is the quote/insight you need to find:
{insight_text}

Please respond in the format: "START: [seconds] END: [seconds]" or "NOT FOUND" if the insight cannot be located."""
        
        response = self.generate_response(prompt, max_tokens=50)
        return self._parse_timestamp_response(response)
    
    def chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """
        Split text into overlapping chunks for processing
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks in characters
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at a sentence boundary
            if end < len(text):
                last_period = text.rfind('.', start, end)
                last_exclamation = text.rfind('!', start, end)
                last_question = text.rfind('?', start, end)
                
                sentence_end = max(last_period, last_exclamation, last_question)
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap if end < len(text) else len(text)
        
        return chunks
    
    def _parse_insights_response(self, response: str, categories: List[str]) -> Dict[str, List[str]]:
        """Parse the insights extraction response"""
        insights = {category: [] for category in categories}
        
        try:
            lines = response.split('\n')
            current_category = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if line is a category header
                is_category = False
                for category in categories:
                    if category.lower() in line.lower() and ':' in line:
                        current_category = category
                        is_category = True
                        break
                
                # Check if line is an insight (starts with -)
                if not is_category and line.startswith('-') and current_category:
                    insight = line[1:].strip()
                    if insight:
                        insights[current_category].append(insight)
        
        except Exception as e:
            logger.error(f"Error parsing insights response: {e}")
        
        return insights
    
    def _parse_timestamp_response(self, response: str) -> tuple[Optional[float], Optional[float]]:
        """Parse timestamp extraction response"""
        try:
            if "NOT FOUND" in response.upper():
                return None, None
            
            # Look for START: and END: patterns
            start_time = None
            end_time = None
            
            if "START:" in response:
                start_part = response.split("START:")[1].split()[0]
                start_time = float(start_part)
            
            if "END:" in response:
                end_part = response.split("END:")[1].split()[0]
                end_time = float(end_part)
            
            return start_time, end_time
        
        except Exception as e:
            logger.error(f"Error parsing timestamp response: {e}")
            return None, None