import os
import subprocess

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

class TTS:
    def text_to_speech(self, text: str, output_path: str, voice: str = "default", language: str = "en") -> bool:
        if GTTS_AVAILABLE:
            return self._gtts(text, output_path, language)
        else:
            return self._windows_tts(text, output_path, language)
    
    def _gtts(self, text: str, output_path: str, language: str) -> bool:
        try:
            lang_map = {
                "tr-TR": "tr",
                "en-US": "en", 
                "en-GB": "en",
                "de-DE": "de",
                "fr-FR": "fr",
                "es-ES": "es"
            }
            
            lang_code = lang_map.get(language, "en")
            tts = gTTS(text=text, lang=lang_code, slow=False)
            tts.save(output_path)
            return os.path.exists(output_path)
        except Exception as e:
            print(f"gTTS Error: {e}")
            return self._windows_tts(text, output_path, language)
    
    def _windows_tts(self, text: str, output_path: str, language: str) -> bool:
        try:
            voice_map = {
                "tr-TR": "Microsoft Tolga Desktop",
                "en-US": "Microsoft David Desktop", 
                "en-GB": "Microsoft Hazel Desktop",
                "de-DE": "Microsoft Stefan Desktop",
                "fr-FR": "Microsoft Paul Desktop",
                "es-ES": "Microsoft Pablo Desktop"
            }
            
            voice_name = voice_map.get(language, "Microsoft David Desktop")
            safe_text = text.replace('"', '`"').replace("'", "''")
            safe_path = output_path.replace('\\', '/')
            
            ps_script = f"""Add-Type -AssemblyName System.Speech; 
            $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; 
            try {{ $synth.SelectVoice('{voice_name}') }} catch {{ }}
            $synth.SetOutputToWaveFile('{safe_path}'); 
            $synth.Speak('{safe_text}'); 
            $synth.Dispose()"""
            
            result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, timeout=30)
            return result.returncode == 0 and os.path.exists(output_path)
        except Exception as e:
            print(f"Windows TTS Error: {e}")
            return False

piper_tts = TTS()