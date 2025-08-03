import pytest
from autonomous_research.generation.content_generator import ContentGenerator

def test_prompt_generation():
    gen = ContentGenerator(model="test-model")
    technique = {"id": "T1003", "name": "OS Credential Dumping", "platform": "Windows"}
    context = "This is a test context."
    for file_name in gen.template_files:
        prompt = gen._get_file_prompt(technique, context, file_name)
        assert isinstance(prompt, str)
        assert "Technique:" in prompt
        assert file_name in prompt or "content for" in prompt

def test_content_quality():
    gen = ContentGenerator()
    good_content = "This is a valid content.\n" * 10 + "Extra details."
    bad_content = "Short."
    placeholder_content = "[To be determined]" + "\n" * 10
    assert gen._validate_content_quality(good_content) is True
    assert gen._validate_content_quality(bad_content) is False
    assert gen._validate_content_quality(placeholder_content) is False
