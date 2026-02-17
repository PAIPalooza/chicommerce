# Audio Transcription Skill

Audio processing workflow:

1. **Analyze File**
   - Use `ffmpeg -i "INPUT_FILE" 2>&1 | grep -E "Duration|Audio"`

2. **Transcode Audio**
   ```bash
   ffmpeg -i "INPUT_FILE" -ar 16000 -ac 1 -c:a pcm_s16le "OUTPUT.wav"
   ```

3. **Whisper Transcription**
   - Models: `tiny` → `large` (increasing accuracy/RAM)
   ```bash
   whisper "AUDIO_FILE.wav" --model base --output_format txt,srt,json
   ```

## Usage Parameters
- Select Whisper model (default: `base`)
- Choose output formats (default: `txt`)
- Preserve transcoded WAV

## Error Handling
- Check ffmpeg/whisper installation
- Validate audio file
- Fallback to smaller models if transcription fails

## Output
1. Audio metadata
2. Transcoded file path
3. Transcription text
4. Generated file paths
5. Processing time