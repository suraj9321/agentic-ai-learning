---
title: Troubleshooting and error codes
updated: 2026-10-02
---
# Troubleshooting and error codes

## The Nimbus bot did not join my meeting

1. Check that your calendar is connected (Settings → Integrations → Calendar).
2. The meeting must have a video link (Zoom, Google Meet or Teams) in the calendar event.
3. Auto-join must be enabled for that meeting type (Settings → Recording → Auto-join).
4. Some companies block external bots in their Zoom settings. Ask the host to admit
   "Nimbus Notetaker" from the waiting room.

## Error codes

**ERR-2201: Rate limit exceeded.** Your workspace sent more than 60 API requests in one
minute. Wait 60 seconds and retry. Use exponential backoff in scripts. Pro workspaces can
ask support to raise the limit to 300 requests per minute.

**ERR-4012: Calendar sync token expired.** Google or Microsoft revoked the access token, which
usually happens after a password change or after 6 months without use. Fix: go to
Settings → Integrations → Calendar, click Disconnect, then Connect again. Meetings scheduled
while the token was expired will not be recorded automatically.

**ERR-4031: Recording permission denied.** The meeting host has disabled recording for
participants. The host must allow recording, or record it themselves.

**ERR-5003: Upload too large.** Manually uploaded audio or video files must be under 2 GB
and shorter than 4 hours. Split longer files, or compress video to audio-only (MP3 or M4A).

**ERR-5100: Transcription failed.** Usually caused by a file with no audio track or an
unsupported codec. Supported formats: MP3, M4A, WAV, MP4, MOV, WEBM.

## Summaries are in the wrong language

Nimbus detects the spoken language automatically. If a meeting mixes languages, set the
language manually in the meeting page → ⋯ → Language. Summaries can be written in a
different language than the meeting: Settings → Summaries → Output language.

## Speaker names are wrong

Speaker names come from the meeting platform. For dial-in participants Nimbus shows
"Speaker 1", "Speaker 2". Click a speaker label in the transcript to rename it; the change
applies to the whole transcript.
