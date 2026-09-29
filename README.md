# higgsfield-api skill

A Claude Code skill for calling the [Higgsfield API](https://docs.higgsfield.ai): image and video models (Seedance, Kling, MiniMax, Wan, Higgsfield Soul and more) with one key, paying per generation.

## Install

Copy the `higgsfield-api/` folder into your project's `.claude/skills/` (or `~/.claude/skills/`).
Set your key with the environment variables `HF_API_KEY_ID` and `HF_API_KEY_SECRET`, or in `~/.secrets/higgsfield-api.json` as `{"key_id": "...", "key_secret": "..."}`. Never commit your key.

Generated files and the request log go to `~/works/data/higgsfield/` (change `DATA_DIR` in `higgsfield-api/scripts/hfapi.py` if you want another place).

## Use

In Claude Code, run `/higgsfield-api` and pick what you want to make.

Shown in this video: https://youtu.be/g1Po3M4FsuU
