"""Mock transcriber for testing"""

from advanced_transcription import AdvancedTranscriptionResult, SpeakerSegment, TimestampedWord

class MockTranscriber:
    def transcribe_with_speaker_diarization(self, audio_path, language=None, use_api=False):
        """Mock transcription for testing"""
        return AdvancedTranscriptionResult(
            text="This is a test transcription of the audio file.",
            language=language or "en",
            confidence=0.95,
            processing_time=2.5,
            model_used="mock",
            speakers=[
                SpeakerSegment(
                    speaker_id="SPEAKER_1",
                    start_time=0.0,
                    end_time=5.0,
                    text="This is a test transcription of the audio file.",
                    confidence=0.95
                )
            ],
            timestamped_words=[
                TimestampedWord("This", 0.0, 0.5, 0.95),
                TimestampedWord("is", 0.5, 0.7, 0.95),
                TimestampedWord("a", 0.7, 0.8, 0.95),
                TimestampedWord("test", 0.8, 1.2, 0.95),
                TimestampedWord("transcription", 1.2, 2.0, 0.95),
                TimestampedWord("of", 2.0, 2.2, 0.95),
                TimestampedWord("the", 2.2, 2.4, 0.95),
                TimestampedWord("audio", 2.4, 2.8, 0.95),
                TimestampedWord("file.", 2.8, 3.0, 0.95),
            ],
            detected_languages=[{"code": "en", "name": "English", "confidence": 0.95}]
        )