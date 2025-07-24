#!/usr/bin/env python3
"""
Test the application without MeiliSearch dependency
This tests the core LLM functionality that was just fixed
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_llm_service():
    """Test the LLM service that was just fixed"""
    print("🤖 Testing LLM Service (recently fixed)...")
    
    try:
        from src.llm_processing.llm_service import LLMService
        
        print("✅ LLM Service imports successfully")
        
        # Initialize the service (this will test model loading)
        print("🔄 Loading LLM model...")
        llm = LLMService()
        
        print(f"✅ Successfully loaded model: {llm.model_name}")
        
        # Test text generation
        print("🧪 Testing text generation...")
        test_prompt = "Please clean and format this text: hello world this is a test"
        response = llm.generate_response(test_prompt, max_tokens=50)
        
        if response:
            print(f"✅ Text generation works!")
            print(f"Response: {response[:100]}...")
        else:
            print("⚠️  Text generation returned empty response")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM Service error: {e}")
        return False

def test_whisper_transcription():
    """Test Whisper transcription service"""
    print("\n🎤 Testing Whisper Transcription...")
    
    try:
        from src.data_ingestion.whisper_transcription import WhisperTranscriptionService
        
        print("✅ Whisper service imports successfully")
        
        # Just test initialization (don't actually transcribe)
        print("🔄 Initializing Whisper...")
        whisper = WhisperTranscriptionService("tiny")  # Use smallest model
        
        print(f"✅ Whisper initialized successfully")
        print(f"Available models: {whisper.get_available_models()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Whisper error: {e}")
        return False

def test_text_processor():
    """Test the text processor without requiring search"""
    print("\n📝 Testing Text Processor...")
    
    try:
        from src.llm_processing.text_processor import TextProcessor
        from src.models.podcast import TranscriptSegment
        
        print("✅ Text Processor imports successfully")
        
        # Create sample segments
        segments = [
            TranscriptSegment(
                text="hello world this is a test segment",
                start_time=0.0,
                end_time=5.0,
                speaker="Speaker 1"
            )
        ]
        
        print("🔄 Initializing Text Processor...")
        # This will also initialize the LLM service
        processor = TextProcessor()
        
        print("✅ Text Processor initialized")
        print(f"Available insight categories: {len(processor.get_insight_categories())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Text Processor error: {e}")
        return False

def main():
    print("🧪 Testing Core Functionality (No MeiliSearch Required)")
    print("=" * 60)
    print("This tests the components that were just fixed.\n")
    
    tests = [
        ("LLM Service", test_llm_service),
        ("Whisper Transcription", test_whisper_transcription),
        ("Text Processor", test_text_processor),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All core components work!")
        print("\n🚀 Next steps:")
        print("   1. Start MeiliSearch: ./start_meilisearch.sh")
        print("   2. Run full demo: python example.py")
        print("   3. Process videos: python run.py process URL --max-videos 2")
    else:
        print("\n⚠️  Some components need attention")
        print("📖 See TROUBLESHOOTING.md for help")
        
        if passed > 0:
            print("\n💡 You can still run:")
            print("   python minimal_demo.py  # Shows data structures")

if __name__ == "__main__":
    main()