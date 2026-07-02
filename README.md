# Faceless Shorts Generator

Give it a text script, get back a 9:16 video that's ready to post. No face, no voice recording, no paid tools.

The chain: a `.txt` script goes through edge-tts for narration (free Microsoft neural voices), Pexels for stock footage (free API), and ffmpeg for the edit — fast cuts, subtle zoom, and word-by-word captions burned in. Out comes an MP4.

## Setup

You'll do this once, takes about ten minutes.

**Requirements**
- Python 3.10+
- ffmpeg on your PATH: `winget install ffmpeg` (Windows), `brew install ffmpeg` (Mac), or `sudo apt install ffmpeg` (Linux)

**Install the packages**
```bash
pip install -r requirements.txt
```

**Get a Pexels API key** (free)

Sign up at https://www.pexels.com/api/, copy your key, and set it as an environment variable:
```bash
# Mac/Linux — add to ~/.zshrc or ~/.bashrc to keep it
export PEXELS_API_KEY="your_key_here"

# Windows PowerShell — then restart the shell
setx PEXELS_API_KEY "your_key_here"
```

**Background music** (optional)

Drop a royalty-free `assets/music.mp3` (YouTube Audio Library has plenty). If it's there it plays quietly under the narration; if not, the video comes out without music.

## Writing a script

Save a `.txt` file in `scripts/`. The format is one search term plus the lines to narrate:

```
[scene: jellyfish underwater glowing | jellyfish tentacles]
This tiny jellyfish has figured out how to never die.

[scene: deep ocean blue]
It reverses its own aging, over and over, forever.
```

- The words inside `[scene: ...]` are the Pexels search. Keep them concrete and filmable — "jellyfish glowing" works, "immortality concept" doesn't. You can pass several terms separated by `|` to pull more varied footage.
- The lines underneath are the narration for that scene.
- Six or seven scenes lands around a 45-second video.

## Running it

```bash
python generate.py scripts/video1_immortal_jellyfish.txt
```

The result shows up at `output/video1_immortal_jellyfish.mp4` — 1080×1920, captioned, ready to upload.

**Options**

```bash
python generate.py scripts/video1.txt --voice en-US-GuyNeural --cut 2.2
```

| Flag | Default | What it does |
|---|---|---|
| `--voice` | `en-US-ChristopherNeural` | any edge-tts voice — run `edge-tts --list-voices` for the full list |
| `--cut` | `2.5` | average clip length in seconds; lower means faster pacing |

Voices worth trying: `en-US-ChristopherNeural` (deep, documentary), `en-US-GuyNeural` (energetic), `en-GB-RyanNeural` (British).

## Troubleshooting

| Problem | Fix |
|---|---|
| "no results on Pexels" | make the search term broader — "bioluminescent polyp" → "jellyfish glowing" |
| voice sounds flat | try a different `--voice`, or tweak the `rate="+8%"` value in `generate.py` |
| captions too big or small | change `SUB_SIZE = 88` near the top of `generate.py` |
| clip doesn't match the topic | narrow the search term, or add a second one after a `|` |
| ffmpeg not found | make sure it's on your PATH and restart the terminal |
| a download hangs | it won't — clips that are too slow or too large get skipped automatically |

## What's next

Things I want to add:

- [ ] AI-generated visuals for abstract ideas that have no good stock footage
- [ ] Script generation built into the pipeline instead of writing them by hand
- [ ] Auto-scheduling to TikTok/Shorts/Reels via the Metricool API
- [ ] Crossfade transitions between scenes

## A note on output

The pipeline does most of the work, but the last 10% is yours: fact-check the script and rewrite at least a line or two in your own words before posting. Fully hands-off content tends to get flagged by the platforms, and a human pass keeps it original.

## License

MIT. Stock footage belongs to its Pexels creators and is free to use under the [Pexels License](https://www.pexels.com/license/).
