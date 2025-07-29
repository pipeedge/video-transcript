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
                if self.device == "cuda":
                    model_kwargs = {
                        "torch_dtype": torch.float16,
                        "device_map": "auto",
                        "low_cpu_mem_usage": True,
                        "trust_remote_code": True
                    }
                else:
                    model_kwargs = {
                        "torch_dtype": torch.float32,
                        "low_cpu_mem_usage": True,
                        "trust_remote_code": True
                    }
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name, 
                    **model_kwargs
                )
                
                # Move model to device if not using device_map
                if self.device != "cuda":
                    self.model = self.model.to(self.device)
                
                # Create text generation pipeline
                self.pipeline = pipeline(
                    "text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=0 if self.device == "cuda" else -1,  # Use explicit device instead of device_map
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
    
    def generate_insight_title(self, insight_text: str) -> str:
        """
        Generate a concise title for an insight using the comprehensive title generation prompt
        
        Args:
            insight_text: The insight content to generate a title for
            
        Returns:
            Generated title (3-5 words, specific and active)
        """
        prompt = f"""# Title Generation
<instructions>
Your goal is to come up with a title for the following insight based off the transcript you've been given.
 
You want the title to be short, but specific. The user should be able to look at the title and understand what the insight is about.
 
Guidelines:
- A generic title is the enemy. Use the unique verbiage of the insight to form the title.
- Don't include 'the' in the title. For example, 'The Importance of Being Early' should just be 'Importance of Being Early'.
- Speak in active voice. For example, 'Importance of Being Early' should be 'Being Early Is Important'.
- Do not use adverbs. For example, 'Wealth Often Precedes Enjoyable Work' should be 'Wealth Precedes Enjoyable Work'. or 'Seamless Waymo Self-Driving Experience in San Francisco' should be 'Waymo in SF'
- Wrap your title in <title> tags. Ex: <title>Employees Show Greatness Early</title>
</instructions>
 
<insight>
{insight_text}
</insight>"""
        
        response = self.generate_response(prompt, max_tokens=30)
        
        # Extract title from <title> tags if present
        if "<title>" in response and "</title>" in response:
            start = response.find("<title>") + 7
            end = response.find("</title>")
            return response[start:end].strip()
        
        # Fallback to the response itself if no tags
        return response.strip()
    
    def create_framework_content(self, transcript_text: str, topic: str) -> str:
        """
        Create structured framework content from transcript text
        
        Args:
            transcript_text: Raw transcript text about a specific topic
            topic: The topic/framework to extract
            
        Returns:
            Structured markdown framework content
        """
        prompt = f"""# Make Framework Content
Your goal is to extract a concise but detailed framework about a topic given a transcript from a podcast. Below you will get a transcript from a user and you want to literally just repeat what the speaker said but in structured markdown.
 
Guidelines
* Remove the fluff - don't pad the text with extra information, only use dense information directly from the transcript
* Bullet points - Use bullet points to describe the key pieces of information
* Use a mix of parent bullets that stand on their own and then bullets that have children when needed
* Start with a mini summary about what the page is about. Keep it short and factual
* Image you are trying to repeat the speaker said but in a more structured and concise way. Use their wording and style.
* Don't start with a title like "Elon Musk's hiring process", just get into the topic summary

<topic>{topic}</topic>
<raw_transcript>
{transcript_text}
</raw_transcript>"""
        
        return self.generate_response(prompt, max_tokens=1000)
    
    def extract_insights(self, text_chunk: str, categories: List[str]) -> Dict[str, List[str]]:
        """
        Extract insights from a text chunk using comprehensive analysis
        
        Args:
            text_chunk: Chunk of transcript text
            categories: List of insight categories to extract
            
        Returns:
            Dictionary with categories as keys and lists of insights as values
        """
        
        prompt = f"""# Insight Extraction
Here is the podcast transcript chunk you need to analyze:
 
<transcript_chunk>
{text_chunk}
</transcript_chunk>
 
You are an expert podcast analyst tasked with extracting key insights from podcast transcripts. Your goal is to provide a clear, concise, and valuable summary of the main points discussed in the podcast.
 
Your task is to carefully read through this transcript and extract key insights, organizing them into the following categories:
 
1. Frameworks and Exercises: Strategies, structured mental models, methods, or mental exercises mentioned for understanding or approaching situations. These should have specific names or clear structures.
 
2. Points of View and Perspectives: Unique opinions, philosophies, or perspectives shared by the speakers. Focus on unpopular or particularly insightful viewpoints.
 
3. Business Ideas: Specific business opportunities proposed as good ways to make money. Only include ideas explicitly presented as business opportunities.
 
4. Stories and Anecdotes: Notable personal experiences or stories about others that illustrate important points or lessons.
 
5. Quotes: Direct quotations from people other than the speakers, used to emphasize points or advance the conversation. Include the person being quoted and the exact words.
 
6. Products: Specific products mentioned by name or with very detailed information.
 
Instructions:
1. Read the transcript carefully, identifying relevant information for each category.
2. For each insight, create a brief title (3-5 words) and a one-sentence description. For quotes, include only the quote and the person being quoted.
3. Ensure each insight is specific, valuable, and distinct. Avoid generic statements like "do better in school."
4. Check that insights do not overlap across categories unless they represent truly distinct entities.
5. Use the same language and vocabulary as the speakers in the transcript.
6. Be thorough in your extraction, aiming to capture all relevant insights.
 
Before providing your final output, wrap your extraction process inside <extraction_process> tags:
<extraction_process>
1. For each category, write down specific examples or quotes from the transcript that fit the category.
2. Review each extracted insight for specificity and value. Refine or remove any that are too generic.
3. Check for category overlap. Ensure each insight is placed in the most appropriate single category.
4. Verify that each insight offers unique information and contributes to understanding the podcast content.
5. Consider the context and background of the podcast to identify any nuanced insights that might not be immediately apparent.
</extraction_process>
 
After your extraction process, present your findings in the following format:
 
---
[Category Name]:
 
* [Brief Title]: [One-sentence description]
* [Another Brief Title]: [One-sentence description]
[Continue for all insights in this category]
 
[Repeat for each category]
---
 
After presenting your findings, reflect on your answer, performing sanity checks and mentioning any additional knowledge or background information which may be relevant.
 
Remember to be specific, avoid overlap, and ensure each insight provides unique value to the reader."""
        
        response = self.generate_response(prompt, max_tokens=1200)
        return self._parse_insights_response(response, categories)
    
    def find_timestamp_for_insight(self, full_transcript: str, insight_text: str) -> tuple[Optional[float], Optional[float]]:
        """
        Find the timestamp for a specific insight in the full transcript using enhanced extraction
        
        Args:
            full_transcript: Full transcript with timestamps
            insight_text: Specific insight text to find
            
        Returns:
            Tuple of (start_time, end_time) or (None, None) if not found
        """
        prompt = f"""# Time Stamp Extraction

Your goal is to extract the start and end timestamps for when a topic is talked about. You want to identify when a topic is first talked about, then when it is done being talked about
Only respond with the timestamps, nothing else.

Here is the full transcript with timestamps:
{full_transcript[:4000]}...

Find the timestamps for this specific insight/topic:
{insight_text}

Respond only with timestamps in the format: START_TIME END_TIME (e.g., 00:59:10 01:02:11)"""
        
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
        """Parse the insights extraction response with enhanced format handling"""
        insights = {category: [] for category in categories}
        
        try:
            # Look for the structured output between --- markers
            if "---" in response:
                # Extract content between --- markers
                parts = response.split("---")
                if len(parts) >= 2:
                    content = parts[1]  # Take the middle part
                else:
                    content = response
            else:
                content = response
            
            lines = content.split('\n')
            current_category = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if line is a category header (ends with :)
                is_category = False
                for category in categories:
                    if (category.lower() in line.lower() and line.endswith(':')) or line.strip() == category:
                        current_category = category
                        is_category = True
                        break
                
                # Check if line is an insight (starts with * or -)
                if not is_category and (line.startswith('*') or line.startswith('-')) and current_category:
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