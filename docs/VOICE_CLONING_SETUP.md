# Voice Cloning Setup Guide

This guide documents how to set up a custom voice clone for the AIQSO AI Phone Assistant using your personal voice recordings.

## Current Status

- **Voice recordings exported**: `/tmp/voice-training/TrainingData/` (10 CAF files, ~25 seconds)
- **Current TTS**: Amazon Polly Neural (Polly.Joanna-Neural)
- **Goal**: Replace with Quinn's cloned voice

## Voice Cloning Options

### Option 1: ElevenLabs (Recommended - Fastest)

**Pros**: Best quality, easy setup, API ready
**Cons**: $5-22/month subscription
**Time to setup**: ~30 minutes

#### Steps:

1. **Convert CAF to WAV**
   ```bash
   # On Mac, convert all CAF files to WAV
   mkdir -p /tmp/voice-wav
   for f in /tmp/voice-training/TrainingData/*.caf; do
     afconvert -f WAVE -d LEI16 "$f" "/tmp/voice-wav/$(basename "$f" .caf).wav"
   done
   ```

2. **Combine into single file** (optional, for better results)
   ```bash
   # Install ffmpeg if needed: brew install ffmpeg
   cd /tmp/voice-wav
   ffmpeg -f concat -safe 0 -i <(for f in *.wav; do echo "file '$PWD/$f'"; done) -c copy combined.wav
   ```

3. **Sign up for ElevenLabs**
   - Go to https://elevenlabs.io
   - Create account ($5/month starter plan)
   - Navigate to "Voice Lab" → "Add Voice" → "Instant Voice Clone"

4. **Upload recordings**
   - Upload the WAV files or combined.wav
   - Add labels: "Quinn", "male", "American"
   - Click "Add Voice"

5. **Get API Key**
   - Go to Profile → API Key
   - Copy the key

6. **Update Phone Assistant**
   ```bash
   # Add to container .env
   ELEVENLABS_API_KEY=your_api_key_here
   ELEVENLABS_VOICE_ID=your_cloned_voice_id
   TTS_PROVIDER=elevenlabs
   ```

7. **Integration code** (to be added to twilio_handler.py)
   ```python
   import requests

   class ElevenLabsTTS:
       def __init__(self, api_key: str, voice_id: str):
           self.api_key = api_key
           self.voice_id = voice_id
           self.base_url = "https://api.elevenlabs.io/v1"

       def generate_speech(self, text: str) -> bytes:
           response = requests.post(
               f"{self.base_url}/text-to-speech/{self.voice_id}",
               headers={
                   "xi-api-key": self.api_key,
                   "Content-Type": "application/json"
               },
               json={
                   "text": text,
                   "model_id": "eleven_monolingual_v1",
                   "voice_settings": {
                       "stability": 0.5,
                       "similarity_boost": 0.75
                   }
               }
           )
           return response.content
   ```

### Option 2: Coqui TTS (Self-Hosted - Free)

**Pros**: Free, runs on AI server, no API limits
**Cons**: Needs more audio (~15-30 min), more setup time
**Time to setup**: ~2-4 hours

#### Steps:

1. **Record more voice samples**
   - Need 15-30 minutes of clear speech
   - Use consistent microphone and environment
   - Read diverse sentences (questions, statements, exclamations)

2. **Install Coqui TTS on AI Server**
   ```bash
   ssh dunkin@192.168.0.234
   pip install TTS
   ```

3. **Prepare training data**
   - Convert recordings to 22050Hz WAV
   - Create metadata.csv with transcriptions
   - Format: `filename|transcription`

4. **Fine-tune model**
   ```bash
   tts --model_name tts_models/en/ljspeech/tacotron2-DDC \
       --config_path config.json \
       --restore_path model.pth \
       --train
   ```

5. **Create TTS API service**
   - Expose as REST API on AI server
   - Integrate with phone assistant

### Option 3: OpenVoice (Self-Hosted - Quick Clone)

**Pros**: Works with 30 seconds of audio, free
**Cons**: Lower quality than ElevenLabs
**Time to setup**: ~1-2 hours

#### Steps:

1. **Install on AI Server**
   ```bash
   ssh dunkin@192.168.0.234
   git clone https://github.com/myshell-ai/OpenVoice.git
   cd OpenVoice
   pip install -e .
   ```

2. **Clone voice**
   ```python
   from openvoice import se_extractor
   from openvoice.api import BaseSpeakerTTS, ToneColorConverter

   # Extract speaker embedding from your recordings
   # Generate speech with your voice tone
   ```

## Recording More Voice Samples

For best results with any voice cloning service, record more samples:

### Recording Guidelines

1. **Environment**
   - Quiet room, no echo
   - Consistent microphone position
   - Same device/mic for all recordings

2. **Content to record**
   - Read news articles aloud
   - Read from audiobook scripts
   - Include questions, statements, exclamations
   - Vary emotions slightly

3. **Technical specs**
   - 44.1kHz or 48kHz sample rate
   - Mono or stereo
   - WAV or high-quality MP3

4. **Duration targets**
   | Service | Minimum | Recommended |
   |---------|---------|-------------|
   | ElevenLabs | 1 min | 30 min |
   | Coqui TTS | 5 min | 30+ min |
   | OpenVoice | 30 sec | 5 min |

### Sample Scripts to Read

Save these to a file and read them aloud:

```
Hello, thank you for calling A.I.Q.S.O. I'm your AI assistant. How can I help you today?

I'd be happy to schedule a consultation for you. What email should I send the calendar invite to?

Our services include AI workflow automation, AI integration, consulting, and custom AI development.

We're located in Dallas-Fort Worth, Texas, and our hours are Monday through Friday, 9 AM to 6 PM Central Time.

I understand you'd like to speak with someone directly. Let me have a team member call you back within the hour.

Thank you for your interest in A.I.Q.S.O. Is there anything else I can help you with today?

That's a great question! Let me explain how our AI automation services work.

I apologize, I didn't quite catch that. Could you please repeat what you said?

Perfect! I've scheduled your consultation. You'll receive a calendar invite shortly.

Thank you for calling A.I.Q.S.O. Have a wonderful day!
```

## Integration Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Twilio    │────▶│ Phone Asst   │────▶│ ElevenLabs API  │
│  (Webhook)  │     │ (Container)  │     │ (Voice Clone)   │
└─────────────┘     └──────────────┘     └─────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Audio URL    │
                    │ (S3/R2/CDN)  │
                    └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Twilio <Play>│
                    │ (TwiML)      │
                    └──────────────┘
```

## Files to Modify

When implementing voice cloning:

1. `src/voice/twilio_handler.py` - Add ElevenLabs/custom TTS support
2. `src/utils/config.py` - Add voice cloning config options
3. `.env` - Add API keys and voice IDs
4. `requirements.txt` - Add `elevenlabs` or `TTS` package

## Cost Comparison

| Solution | Monthly Cost | Quality | Latency |
|----------|-------------|---------|---------|
| Polly Neural (current) | ~$4/1M chars | Good | Low |
| ElevenLabs Starter | $5/mo (30K chars) | Excellent | Medium |
| ElevenLabs Creator | $22/mo (100K chars) | Excellent | Medium |
| Coqui (self-hosted) | $0 (GPU cost) | Good | Low |
| OpenVoice (self-hosted) | $0 (GPU cost) | Fair | Low |

## Next Steps Checklist

- [ ] Record additional voice samples (15-30 minutes)
- [ ] Convert CAF files to WAV format
- [ ] Sign up for ElevenLabs or set up self-hosted solution
- [ ] Upload voice samples and create voice clone
- [ ] Test voice clone quality
- [ ] Integrate with phone assistant
- [ ] Update Twilio handler to use custom TTS
- [ ] Test end-to-end phone call with cloned voice

## Resources

- [ElevenLabs Documentation](https://docs.elevenlabs.io/)
- [Coqui TTS GitHub](https://github.com/coqui-ai/TTS)
- [OpenVoice GitHub](https://github.com/myshell-ai/OpenVoice)
- [Twilio TwiML Play](https://www.twilio.com/docs/voice/twiml/play)
