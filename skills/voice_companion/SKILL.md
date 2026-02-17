# Skill: voice_companion

## Description
Angela's voice mode — natural Thai/English conversation via wake word detection, STT, and TTS.

## Triggers
- event: voice.wake_word_detected

## Tools
- start_session: Start a voice conversation session with David
  - parameters: {}
  - handler: handler.py::start_session

## Config
- wake_words: angela, น้อง, angie
- thai_voice: Kanya
- english_voice: Samantha
- max_turns: 20
