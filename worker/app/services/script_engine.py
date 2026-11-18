import json
from typing import Dict, Any, List
import httpx

from app.config import settings
from app.schemas import SceneSpec


class ScriptEngine:
    """
    Hollywood-Grade Documentary Script & Scene Director Engine.
    Uses Gemini REST API or built-in master templates to generate cinematic shot lists
    with explicit camera motion vectors, lighting, and sound design cues.
    """

    SYSTEM_PROMPT = """You are an elite Hollywood Science Documentary Showrunner and Lead Cinematographer (BBC Horizon, Cosmos: Possible Worlds, Christopher Nolan aesthetic).
Your task is to craft deeply researched, immersive, cinematic documentary scripts and shot plans for VOIDORA.

Cinematic Standards:
- NEVER design static slideshows or simple flat picture zooms.
- Every scene must be planned as a dynamic movie shot with explicit camera motion, lighting, and atmospheric dynamics (fog, dust motes, stellar drift, mechanical motion).
- Differentiate between:
  1. "AI_CINEMATIC": Original photorealistic movie scenes generated with modern AI video models (Kling, Runway Gen-3, Luma Ray 2).
  2. "ARCHIVAL_AUTHENTIC": Genuine historical documents, logs, and photos (e.g., Jerry Ehman's Wow! signal printout, Apollo transcripts) where scientific truth matters.
  3. "NASA_SCIENTIFIC": Authentic space agency telescopic footage and planetary surveys.
- Camera movements must be cinematic: slow_push_in, dolly_tracking, wide_aerial, orbital_arc, macro_close_up.
- Audio cues (sfx_cue) must specify atmospheric sound design (tape flutter, cosmic drone, radio static sweep).
- Output MUST be valid JSON adhering strictly to the requested schema.
"""

    async def generate_documentary_plan(self, niche: str, title_concept: str, target_format: str = "LONG_FORM") -> Dict[str, Any]:
        """
        Generates narrative script and director-grade scene breakdown.
        """
        target_minutes = 8 if target_format == "LONG_FORM" else 1

        prompt = f"""Write a master Hollywood cinematic documentary plan for:
Niche: {niche}
Title: {title_concept}
Target Duration: ~{target_minutes} minutes

Output a JSON object with:
{{
  "title": "{title_concept}",
  "seo_description": "Comprehensive YouTube description...",
  "tags": ["Space", "Astronomy", "VOIDORA", "Cosmic Mystery", "Science Documentary"],
  "narration_full": "The complete narrative text to be read by the narrator...",
  "scenes": [
    {{
      "scene_index": 1,
      "narration_segment": "Segment text read during this scene...",
      "shot_type": "AI_CINEMATIC",
      "visual_description": "Cinematic visual description of footage needed...",
      "ai_prompt": "Ultra-detailed photorealistic cinematic prompt with lighting, camera lens, resolution, and motion...",
      "camera_motion": "slow_push_in",
      "visual_lighting": "Volumetric moonlight cutting through rolling ground mist...",
      "sfx_cue": "Low sub-bass drone and gentle night wind...",
      "search_keywords": ["big ear telescope", "radio observatory", "deep space night"],
      "duration_seconds": 8.0
    }}
  ]
}}
"""

        # If Gemini API key is configured, invoke Gemini via REST API
        if settings.GEMINI_API_KEY:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "systemInstruction": {"parts": [{"text": self.SYSTEM_PROMPT}]},
                    "generationConfig": {"responseMimeType": "application/json"}
                }
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        return json.loads(raw_text)
            except Exception:
                pass  # Fallback to master director templates

        # Master Director Template: The Wow! Signal — The 72-Second Mystery From Space
        if "wow" in title_concept.lower() or "signal" in title_concept.lower():
            return {
                "title": "The Wow! Signal — The 72-Second Mystery From Space",
                "seo_description": (
                    "On August 15, 1977, a radio telescope in Ohio picked up a 72-second signal from the depths of space "
                    "that remains humanity's greatest unsolved cosmic mystery. This is the story of the Wow! Signal.\n\n"
                    "#VOIDORA #WowSignal #Astronomy #CosmicMystery #SETI #ScienceDocumentary"
                ),
                "tags": ["Wow Signal", "SETI", "Space Mystery", "Radio Astronomy", "Big Ear", "VOIDORA", "Aliens"],
                "narration_full": (
                    "In the late summer of 1977, in a quiet clearing outside Delaware, Ohio, humanity’s most sensitive ear to the cosmos was listening. "
                    "There were no flashing lights. No sirens. Only the quiet, rhythmic whir of magnetic tape and the relentless chatter of an IBM mainframe. "
                    "As the Earth rotated, the Big Ear telescope’s dual feed horns swept across the constellation Sagittarius. For exactly seventy-two seconds, the cosmos screamed. "
                    "Days later, astronomer Jerry Ehman was reviewing the computer printout. Amidst the sea of baseline ones and twos, a sequence of alphanumeric characters leaped off the page: 6EQUJ5. "
                    "It was transmitted at 1420.4 megahertz—the universal calling card of neutral hydrogen. "
                    "Decades have passed. Every effort to re-detect the signal has failed. Was it a passing comet, a secret terrestrial reflection, or a civilization reaching out across the dark abyss?"
                ),
                "scenes": [
                    {
                        "scene_index": 1,
                        "narration_segment": "In the late summer of 1977, in a quiet clearing outside Delaware, Ohio, humanity’s most sensitive ear to the cosmos was listening.",
                        "shot_type": "AI_CINEMATIC",
                        "visual_description": "Wide aerial establishing shot of the Big Ear radio observatory at 2:00 AM surrounded by misty fields.",
                        "ai_prompt": "Cinematic IMAX 70mm footage, establishing aerial wide shot. The Big Ear radio observatory in 1977 rural Ohio at 2:00 AM. Massive flat reflector mesh antennas towering over misty fields. Moonlight cutting through dense atmospheric ground fog. Volumetric moonlight, slow cinematic forward dolly tracking shot. Realistic deep space sky full of stars. Photorealistic, hyper-detailed, Panavision anamorphic lens flare, 4k resolution, 35mm film grain.",
                        "camera_motion": "wide_aerial",
                        "visual_lighting": "Volumetric moonlight through rolling ground fog, soft silver rim lighting",
                        "sfx_cue": "Gentle night wind, distant crickets, low sub-bass drone",
                        "search_keywords": ["big ear radio telescope", "radio observatory night", "astronomy observatory"],
                        "duration_seconds": 8.0
                    },
                    {
                        "scene_index": 2,
                        "narration_segment": "There were no flashing lights. No sirens. Only the quiet, rhythmic whir of magnetic tape and the relentless chatter of an IBM mainframe.",
                        "shot_type": "AI_CINEMATIC",
                        "visual_description": "Interior of 1970s computer room with spinning magnetic tape reels and glowing green CRT monitor.",
                        "ai_prompt": "Cinematic close-up tracking shot inside a dark 1970s radio astronomy laboratory at night. An IBM mainframe reel-to-reel tape deck spinning smoothly, green phosphor CRT monitor glowing on the control desk. Dusty air particles illuminated by amber indicator lights. Slow cinematic push-in, shallow depth of field, anamorphic bokeh, authentic period-accurate scientific equipment, photorealistic, 8k.",
                        "camera_motion": "dolly_tracking",
                        "visual_lighting": "Green CRT phosphor glow and amber indicator lamps in deep shadows",
                        "sfx_cue": "Analog magnetic tape flutter and mechanical relay clicks",
                        "search_keywords": ["1970s mainframe computer", "reel to reel tape drive", "vintage computer room"],
                        "duration_seconds": 7.5
                    },
                    {
                        "scene_index": 3,
                        "narration_segment": "As the Earth rotated, the Big Ear telescope’s dual feed horns swept across the constellation Sagittarius. For exactly seventy-two seconds, the cosmos screamed.",
                        "shot_type": "AI_CINEMATIC",
                        "visual_description": "Majestic orbital camera motion past the telescope feed horns looking out toward the glittering stars of Sagittarius.",
                        "ai_prompt": "Cinematic IMAX space shot. A massive parabolic radio telescope receiver horn silhouetted against the dense star clouds of the Sagittarius constellation. Slow orbital camera motion revealing the sheer scale of the cosmos. Subtle volumetric atmospheric light refractions, dynamic star twinkling, dust nebulae glowing faintly in the distance. 35mm film look, Christopher Nolan documentary style, ultra-realistic.",
                        "camera_motion": "orbital_arc",
                        "visual_lighting": "Starlight and glowing cosmic dust reflecting off metallic feed horns",
                        "sfx_cue": "Rising electromagnetic harmonic resonance at 1420 MHz",
                        "search_keywords": ["sagittarius constellation stars", "radio telescope antenna", "deep space stars"],
                        "duration_seconds": 9.0
                    },
                    {
                        "scene_index": 4,
                        "narration_segment": "Days later, astronomer Jerry Ehman was reviewing the computer printout. Amidst the sea of baseline ones and twos, a sequence of alphanumeric characters leaped off the page: 6EQUJ5.",
                        "shot_type": "ARCHIVAL_AUTHENTIC",
                        "visual_description": "Extreme close-up macro push-in on the authentic 1977 computer printout showing 6EQUJ5 circled in red pen with the word Wow!",
                        "ai_prompt": "Cinematic macro shot of vintage 1977 dot-matrix green-bar computer paper. The alphanumeric sequence 6EQUJ5 circled boldly in red ink pen with the handwritten word Wow in the margin. High texture paper grain, dramatic side lighting casting subtle shadows across the paper creases, 4k ultra-sharp documentary detail.",
                        "camera_motion": "macro_close_up",
                        "visual_lighting": "Warm incandescent desk lamp raking across textured paper",
                        "sfx_cue": "Paper rustle and sharp breath intake",
                        "search_keywords": ["wow signal printout 6equj5", "jerry ehman wow signal", "big ear printout"],
                        "duration_seconds": 8.5
                    },
                    {
                        "scene_index": 5,
                        "narration_segment": "It was transmitted at 1420.4 megahertz—the universal calling card of neutral hydrogen.",
                        "shot_type": "AI_CINEMATIC",
                        "visual_description": "Photorealistic visualization of a coherent radio wave propagating through deep interstellar hydrogen gas.",
                        "ai_prompt": "Photorealistic cinematic science documentary scene. A coherent electromagnetic radio wave propagating through a deep space nebula of cold neutral hydrogen. Volumetric ionization glow, realistic cosmic dust particles drifting in zero gravity, deep blues and glowing warm hydrogen-alpha magenta light. Slow cinematic dolly-in, IMAX camera realism, scientific accuracy.",
                        "camera_motion": "slow_push_in",
                        "visual_lighting": "Luminescent hydrogen-alpha glow and coherent wave energy",
                        "sfx_cue": "Pure resonant 1420 Hz sine tone harmonic chime",
                        "search_keywords": ["interstellar gas nebula", "hydrogen emission nebula", "cosmic radio waves"],
                        "duration_seconds": 7.5
                    },
                    {
                        "scene_index": 6,
                        "narration_segment": "Decades have passed. Every effort to re-detect the signal has failed. Was it a passing comet, a secret terrestrial reflection, or a civilization reaching out across the dark abyss?",
                        "shot_type": "AI_CINEMATIC",
                        "visual_description": "Creeping camera push into the pitch-black void of Sagittarius, lonely stars receding into infinity.",
                        "ai_prompt": "Cinematic deep space journey shot. Camera pushing slowly into the dark void between the stars of Sagittarius. Faint, lonely star systems drifting past the frame with smooth parallax. Cold, haunting cinematic lighting, volumetric starlight, realistic dark interstellar dust clouds, Interstellar movie aesthetic, 4k ultra-photorealism.",
                        "camera_motion": "slow_push_in",
                        "visual_lighting": "Cold pinpoint starlight against the deep black abyss",
                        "sfx_cue": "Fading radio static dissolving into solitary resonant cello",
                        "search_keywords": ["dark space void", "deep universe stars", "sagittarius starry abyss"],
                        "duration_seconds": 9.5
                    }
                ]
            }

        # Default Master Director Template: The Great Attractor
        return {
            "title": title_concept,
            "seo_description": f"An in-depth documentary exploring {title_concept}. Subscribe to VOIDORA for daily cinematic science and cosmic mysteries.\n\n#VOIDORA #Science #Documentary",
            "tags": ["VOIDORA", "Space", "Astronomy", "Cosmic Mystery", "Science Documentary"],
            "narration_full": (
                "Deep in the cosmic ocean, hundreds of millions of light-years from Earth, something impossible is pulling our entire galaxy. "
                "Every star, every planet, and every particle of the Milky Way is speeding toward a hidden gravitational anomaly known as the Great Attractor. "
                "Yet, despite our most powerful telescopes, what lies at the heart of this colossal cosmic pull remains hidden behind the Zone of Avoidance."
            ),
            "scenes": [
                {
                    "scene_index": 1,
                    "narration_segment": "Deep in the cosmic ocean, hundreds of millions of light-years from Earth, something impossible is pulling our entire galaxy.",
                    "shot_type": "AI_CINEMATIC",
                    "visual_description": "Slow camera drift through a hyper-realistic starfield and cosmic dust.",
                    "ai_prompt": "Cinematic IMAX space shot. Camera slowly drifting forward through deep space star clusters and cosmic dust filaments. Volumetric starlight, rich shadows, 8k resolution, photorealistic, Panavision lens.",
                    "camera_motion": "slow_push_in",
                    "visual_lighting": "Volumetric starlight and rim-lit cosmic dust filaments",
                    "sfx_cue": "Deep cosmic sub-bass rumble",
                    "search_keywords": ["deep space stars", "galaxy cosmic nebula", "night sky universe"],
                    "duration_seconds": 8.5
                },
                {
                    "scene_index": 2,
                    "narration_segment": "Every star, every planet, and every particle of the Milky Way is speeding toward a hidden gravitational anomaly known as the Great Attractor.",
                    "shot_type": "AI_CINEMATIC",
                    "visual_description": "Spiral galaxy rotating slowly with gravitational vector lines or motion trails.",
                    "ai_prompt": "Cinematic wide shot of the Milky Way spiral galaxy rotating in space. Glowing core, intricate dust lanes, slow orbital camera movement with realistic parallax, hyper-detailed physics.",
                    "camera_motion": "orbital_arc",
                    "visual_lighting": "Brilliant galactic nucleus glow and deep interstellar shadows",
                    "sfx_cue": "Ethereal gravitational hum",
                    "search_keywords": ["milky way galaxy", "gravitational pull", "cosmic gravity"],
                    "duration_seconds": 9.0
                },
                {
                    "scene_index": 3,
                    "narration_segment": "Yet, despite our most powerful telescopes, what lies at the heart of this colossal cosmic pull remains hidden behind the Zone of Avoidance.",
                    "shot_type": "AI_CINEMATIC",
                    "visual_description": "Giant radio telescope dish gazing toward dark nebulae and hidden clusters.",
                    "ai_prompt": "Dramatic wide shot of a modern radio telescope array pointing up into a dark, impenetrable cosmic dust wall. Dramatic atmospheric lighting, sharp silhouette, photorealistic, 4k.",
                    "camera_motion": "wide_aerial",
                    "visual_lighting": "Dramatic silhouette against starry night sky",
                    "sfx_cue": "Mechanical telescope drive tracking hum",
                    "search_keywords": ["radio telescope", "observatory space", "dark nebula"],
                    "duration_seconds": 9.5
                }
            ]
        }


script_engine = ScriptEngine()
