#!/usr/bin/env python3
"""
Demo script for Advanced NER functionality
Tests the GPT-powered entity extraction and script generation
"""

import os
from dotenv import load_dotenv
from ner_advanced import (
    extract_entities_advanced, 
    generate_script, 
    analyze_sentiment,
    get_fallback_suggestions,
    AdvancedNERError
)

# Load environment variables
load_dotenv()

def demo_entity_extraction():
    """Demo advanced entity extraction"""
    print("=== Advanced Entity Extraction Demo ===")
    
    sample_text = """
    Yesterday, CEO Sarah Johnson announced that TechCorp has secured a $50 million 
    investment from Goldman Sachs. The funding will be used to expand operations 
    in San Francisco and hire 200 new engineers by Q2 2024. The company, founded 
    in 2019, has grown from 10 to 500 employees and now serves over 10,000 customers 
    worldwide. "This investment validates our AI-first approach," said Johnson during 
    the press conference at the company's headquarters.
    """
    
    try:
        entities, summary = extract_entities_advanced(sample_text)
        
        print(f"Summary: {summary}\n")
        
        for category, items in entities.items():
            if items:  # Only show categories with entities
                print(f"{category.upper()}:")
                for item in items:
                    print(f"  - {item}")
                print()
                
    except AdvancedNERError as e:
        print(f"Error: {e}")
        print("\nFallback suggestions:")
        for suggestion in get_fallback_suggestions():
            print(f"  - {suggestion}")

def demo_script_generation():
    """Demo script generation for admin content"""
    print("=== Script Generation Demo ===")
    
    prompt = "Create a conversation about the benefits of renewable energy"
    
    try:
        script = generate_script(prompt, style="conversational")
        print(f"Generated Script:\n{script}")
        
    except AdvancedNERError as e:
        print(f"Error: {e}")
        print("\nFallback suggestions:")
        for suggestion in get_fallback_suggestions():
            print(f"  - {suggestion}")

def demo_sentiment_analysis():
    """Demo sentiment analysis"""
    print("=== Sentiment Analysis Demo ===")
    
    test_texts = [
        "I absolutely love this new product! It's amazing and works perfectly.",
        "This is terrible. Nothing works as expected and I'm very disappointed.",
        "The weather is okay today. Nothing special, just a regular day."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nText {i}: {text}")
        
        try:
            sentiment = analyze_sentiment(text)
            print(f"Sentiment Analysis:")
            print(f"  Positive: {sentiment['positive']:.2f}")
            print(f"  Negative: {sentiment['negative']:.2f}")
            print(f"  Neutral: {sentiment['neutral']:.2f}")
            print(f"  Confidence: {sentiment['confidence']:.2f}")
            
        except AdvancedNERError as e:
            print(f"Error: {e}")

def main():
    """Run all demos"""
    print("Advanced NER Module Demo")
    print("=" * 50)
    
    # Check if API key is configured
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OpenAI API key not found!")
        print("Please set OPENAI_API_KEY in your .env file to run the demos.")
        print("\nYou can still run the tests with mock responses:")
        print("python -m pytest test_ner_advanced.py -v")
        return
    
    print("✅ OpenAI API key found. Running demos...\n")
    
    try:
        demo_entity_extraction()
        print("\n" + "="*50 + "\n")
        
        demo_script_generation()
        print("\n" + "="*50 + "\n")
        
        demo_sentiment_analysis()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("This might be due to API rate limits or network issues.")

if __name__ == "__main__":
    main()