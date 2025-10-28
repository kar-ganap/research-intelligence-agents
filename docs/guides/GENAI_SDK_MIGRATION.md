# Google GenAI SDK Migration Guide

This project uses the **new unified Google GenAI SDK** (`google-genai`) instead of the deprecated `google-generativeai` package.

---

## 📋 What Changed?

### OLD (Deprecated - End of Support: Aug 31, 2025)
```python
import google.generativeai as genai

genai.configure(api_key='YOUR_API_KEY')
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content('Hello')
```

### NEW (Current - GA since May 2025)
```python
from google import genai

client = genai.Client(api_key='YOUR_API_KEY')
response = client.models.generate_content(
    model='gemini-2.0-flash-exp',
    contents='Hello'
)
print(response.text)
```

---

## 🎯 Key Differences

| Feature | Old SDK | New SDK |
|---------|---------|---------|
| **Package** | `google-generativeai` | `google-genai` |
| **Import** | `import google.generativeai as genai` | `from google import genai` |
| **Client** | Global configuration | Client instance |
| **Models** | `GenerativeModel()` | `client.models` |
| **Status** | Deprecated | GA (General Availability) |
| **Support Ends** | August 31, 2025 | Active |

---

## 🚀 Installation

```bash
# Install new SDK
uv pip install google-genai

# Uninstall old SDK (if present)
uv pip uninstall google-generativeai
```

---

## 💡 Usage Examples

### Basic Text Generation

```python
from google import genai

# Create client
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

# Generate content
response = client.models.generate_content(
    model='gemini-2.0-flash-exp',
    contents='Explain quantum computing in simple terms'
)

print(response.text)
```

### Streaming Response

```python
response = client.models.generate_content_stream(
    model='gemini-2.0-flash-exp',
    contents='Write a short story'
)

for chunk in response:
    print(chunk.text, end='')
```

### With System Instructions

```python
response = client.models.generate_content(
    model='gemini-2.0-flash-exp',
    contents='What is photosynthesis?',
    config={
        'system_instruction': 'You are a biology teacher. Explain concepts clearly and concisely.',
        'temperature': 0.7,
        'max_output_tokens': 1024,
    }
)
```

### Using Vertex AI

```python
# For Vertex AI (instead of Developer API)
client = genai.Client(
    vertexai=True,
    project='your-project-id',
    location='us-central1'
)

response = client.models.generate_content(
    model='gemini-2.0-flash-exp',
    contents='Hello from Vertex AI'
)
```

### List Available Models

```python
models = client.models.list()
for model in models:
    if 'gemini' in model.name.lower():
        print(f"Model: {model.name}")
        print(f"  Display Name: {model.display_name}")
        print(f"  Supported: {model.supported_generation_methods}")
```

---

## 🏗️ Project Usage

### Agent Configuration

When creating agents in this project, use the new SDK:

```python
from google import genai
from google.adk import Agent

# Create Gemini client
gemini_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

# Use with ADK agents
agent = Agent(
    name='research_agent',
    model='gemini-2.0-flash-exp',
    # ... other config
)
```

### In Tools and Utilities

```python
# src/utils/gemini_client.py
import os
from google import genai

def get_gemini_client():
    """Get configured Gemini client."""
    api_key = os.getenv('GEMINI_API_KEY')
    return genai.Client(api_key=api_key)

def generate_response(prompt: str, model: str = 'gemini-2.0-flash-exp'):
    """Generate response using Gemini."""
    client = get_gemini_client()
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )
    return response.text
```

---

## ⚠️ Breaking Changes

1. **No global configuration**: Must create a `Client` instance
2. **Different model access**: Use `client.models` instead of `GenerativeModel()`
3. **Response structure**: Slightly different response object structure
4. **Method names**: Some methods renamed (e.g., `generate_content_stream`)

---

## 📚 Resources

- [Official Migration Guide](https://medium.com/google-cloud/migrating-to-the-new-google-gen-ai-sdk-python-074d583c2350)
- [New SDK GitHub](https://github.com/googleapis/python-genai)
- [API Documentation](https://ai.google.dev/gemini-api/docs/libraries)
- [Gemini API Docs](https://ai.google.dev/)

---

## ✅ Migration Checklist

For this project, the following have been updated:

- [x] Updated `pyproject.toml` to use `google-genai>=1.0.0`
- [x] Updated `test_setup.py` to test new SDK
- [x] Updated `.env.example` with proper key naming
- [x] All tests passing with new SDK (8/8 ✅)

When writing new code:
- [ ] Use `from google import genai` for imports
- [ ] Create `Client` instances instead of global config
- [ ] Use `client.models.generate_content()` pattern
- [ ] Reference this guide for examples

---

**Last Updated**: 2025-10-28
**SDK Version**: google-genai >= 1.0.0
