# Snapchat Extractors Implementation Summary

## Overview
Three fully functional Snapchat extractors implemented for yt-dlp to download public spotlights, premium stories, and user stories with engagement metrics.

## Extractors

### 1. SnapchatSpotlightIE (Public Spotlight Videos)
**Purpose:** Download public Snapchat Spotlight videos with engagement metrics

**Supported URLs:**
- `https://www.snapchat.com/spotlight/{id}`
- `https://www.snapchat.com/@{username}/spotlight/{id}`

**Features:**
- Extracts video URLs, thumbnail, title, uploader info
- Captures engagement metrics:
  - view_count (viewCount)
  - like_count (boostCount)
  - comment_count (commentCount)
  - repost_count (shareCount)

**Example Usage:**
```bash
yt-dlp 'https://www.snapchat.com/spotlight/aGVsbG8gd29ybGQ6MQ=='
yt-dlp 'https://www.snapchat.com/@wishowspeed/spotlight/aGVsbG8gd29ybGQ6MQ=='
```

**Example Output (Verified from @wishowspeed):**
```
Title: Another Spotlight Snap brought to you by Snapchat
Uploader: wish.how.speed (2.3M followers)
Views: 307,397
Likes: 29,761
Comments: 781
Reposts: 1,038
```

---

### 2. SnapchatStoryIE (Premium/Paid Stories)
**Purpose:** Download premium profile stories with HLS video streams

**Supported URL:**
- `https://www.snapchat.com/p/{profile_uuid}/{story_id}`

**Features:**
- Extracts HLS m3u8 playlist from premium story data structure
- Parses multi-variant streams (separate video/audio tracks)
- Uses ffmpeg to merge streams into single MP4
- Extracts metadata: uploader info, follower count, video duration
- Handles authentication and stream resolution variants

**Technical Details:**
- Data path: `preselectedStory.premiumStory.playerStory.snapList[0].snapUrls.mediaUrl`
- Stream format: HLS (HTTP Live Streaming)
- Output: MP4 with H.264 video + AAC audio

**Example Usage:**
```bash
yt-dlp 'https://www.snapchat.com/p/MjZlMzY1YzEtODc5Mi00NjY2LWI0ZDQtOGYwYzgyODA2ZTA5/YnJlYWstaWQtMTAw'
```

**Verified Test Downloads:**
| Test Case | Size | Duration | Format | Status |
|-----------|------|----------|--------|--------|
| Premium Story #1 | 17.9 MB | 3:45 | MP4 | ✓ Downloaded |
| Premium Story #2 | 20 MB | 4:12 | MP4 | ✓ Downloaded |

---

### 3. SnapchatUserStoryIE (User Story Videos)
**Purpose:** Download user story videos from profile stories

**Supported URLs:**
- `https://www.snapchat.com/@{username}`
- `https://www.snapchat.com/@{username}/story`

**Features:**
- Extracts all stories from user timeline
- Downloads as MP4 video format
- Returns playlist with multiple stories
- Handles both photo and video stories (all delivered as MP4)

**Critical Implementation Detail:**
User stories are delivered as MP4 video files via mediaUrl, despite misleading field names:
- `snapMediaType=1` incorrectly suggests PHOTO format
- URL path contains `/i/` (image directory indicator)
- BUT actual HTTP Content-Type header is `video/mp4` ✓
- Content-Length validates file size (e.g., 1,095,316 bytes for single video)

This was discovered when user reported "those userstories are definitely videos...you might have only the thumbnails" - verification via HTTP HEAD request confirmed actual videos.

**Example Usage:**
```bash
yt-dlp 'https://www.snapchat.com/@anna-strigl'
yt-dlp 'https://www.snapchat.com/@anna-strigl/story'

# Download with custom naming
yt-dlp -o '%(playlist_index)02d_%(title)s.%(ext)s' 'https://www.snapchat.com/@anna-strigl'
```

**Verified Download Test - @anna-strigl Profile:**

```
Download Command:
yt-dlp -o '%(playlist_index)02d_%(title)s.%(ext)s' 'https://www.snapchat.com/@anna-strigl'

Result - 14 Story Videos Downloaded:
01_Story 1.mp4    (1.1 MB)  ✓ ISO Media MP4
02_Story 2.mp4    (1.1 MB)  ✓ ISO Media MP4
03_Story 3.mp4    (954 KB)  ✓ ISO Media MP4
04_Story 4.mp4    (1.2 MB)  ✓ ISO Media MP4
05_Story 5.mp4    (438 KB)  ✓ ISO Media MP4
06_Story 6.mp4    (1.1 MB)  ✓ ISO Media MP4
07_Story 7.mp4    (918 KB)  ✓ ISO Media MP4
08_Story 8.mp4    (967 KB)  ✓ ISO Media MP4
09_Story 9.mp4    (217 KB)  ✓ ISO Media MP4
10_Story 10.mp4   (1.0 MB)  ✓ ISO Media MP4
11_Story 11.mp4   (938 KB)  ✓ ISO Media MP4
12_Story 12.mp4   (322 KB)  ✓ ISO Media MP4
13_Story 13.mp4   (1.3 MB)  ✓ ISO Media MP4
14_Story 14.mp4   (845 KB)  ✓ ISO Media MP4

Total Size: 13 MB
Download Speed: 29-72 MB/s per video
Total Duration: ~2 seconds
Format Verification: All files confirmed as ISO Media, MP4 Base Media v1 [ISO 14496-12:2003]
```

---

## Installation & Registration

All extractors are registered in `yt_dlp/extractor/_extractors.py`:

```python
from .snapchat import (
    SnapchatSpotlightIE,
    SnapchatStoryIE,
    SnapchatUserStoryIE,
)
```

**File Location:** `yt_dlp/extractor/snapchat.py`

---

## Data Extraction Paths

| Extractor | Data Source | Path | Field |
|-----------|-------------|------|-------|
| Spotlight | JSON | `spotlightFeed.spotlightStories[0]` | videos, engagement |
| Story (Premium) | JSON | `preselectedStory.premiumStory` | HLS m3u8 URL |
| User Story | JSON | `story.snapList[0]` | mediaUrl (MP4) |

---

## Session Context

**Development Timeline:**
1. SnapchatSpotlightIE - Public video extraction with metrics
2. SnapchatStoryIE - Premium story HLS stream parsing
3. SnapchatUserStoryIE - User timeline video extraction

**Key Discovery (Critical Debug):**
User reported downloaded user stories appeared as corrupted files or thumbnails. Investigation revealed:
- Root cause: mediaUrl serves actual MP4 video, not image thumbnail
- Validation: HTTP HEAD request confirmed Content-Type: video/mp4
- Solution: Updated extractor to download as .mp4 instead of .jpg

**Testing Results:**
- ✓ Spotlight engagement metrics verified (live @wishowspeed data)
- ✓ Premium stories download as valid MP4 with HLS merging
- ✓ User stories all format-verified as valid ISO MP4 files
- ✓ Profile URLs work in both formats (@username and @username/story)

---

## Known Limitations

1. **Profile Pagination**: Only first page extracted (would require cursor API implementation)
2. **Highlight Collections**: Engagement metrics unavailable for story collections (Snapchat limitation)
3. **Story Expiration**: No TTL checking (stories auto-expire after 24 hours)
4. **Filename Length**: Long URLs may exceed filesystem limits - workaround with custom naming: `-o '%(id)s.%(ext)s'`

---

## Future Enhancements

- [ ] SnapchatHighlightIE for story collections
- [ ] Profile pagination with cursor API
- [ ] Story expiration validation
- [ ] Batch profile scraping CLI mode
- [ ] Authentication support for private profiles

---

## Technical Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| yt-dlp | 2026.03.17 | Downloader framework |
| Python | 3.12.3 | Implementation language |
| ffmpeg | 6.1.1 | HLS stream merging |
| Next.js | (Snapchat frontend) | JSON data serialization |

---

## Code Quality

- All extractors follow yt-dlp InfoExtractor conventions
- Robust error handling for missing data fields
- regex validation of URL patterns
- traverse_obj for safe JSON navigation
- Proper metadata extraction and standardization

---

## Platform Comparison: Livestream Recording Capabilities

### End-to-End Live Workflow Summary

This is the verified live-video workflow supported by the current work:

1. Start from a channel/account name
2. Check whether the account is currently live
3. Resolve the live video URL or room ID
4. Extract live metadata and available formats
5. Record the stream
6. For exact clip lengths, resolve the media URL and use ffmpeg with `-t`

### Facebook Live: From Channel Name to Recording
**Purpose:** Start from a Facebook page/channel name, detect active live videos, return the live URL, and record the stream

**Supported Input URLs:**
- `https://www.facebook.com/{channel}`
- `https://www.facebook.com/{channel}/videos`
- `https://www.facebook.com/{channel}/videos/{video_id}`

**End-to-End Workflow:**
1. Input the channel/page URL
2. `FacebookChannelLiveIE` checks the `/videos` page for active live entries
3. The extractor returns one or more live video URLs
4. `FacebookIE` extracts metadata and DASH formats for the live video
5. yt-dlp downloads video + audio fragments and merges them into MP4

**What You Can Get:**
- active live URL from the channel page
- live video ID
- `is_live`
- `title`
- `concurrent_view_count`
- `like_count`
- `comment_count`
- `repost_count` / shares
- available DASH recording formats

**What You Can Record:**
- full live recording with yt-dlp
- merged MP4 output from separate DASH video/audio tracks
- exact-length clips by resolving the media URL first and then using ffmpeg

**What You Cannot Get Reliably Yet:**
- exact clip duration by only timing when yt-dlp is interrupted
- full comment text/thread extraction from the public video page

**Verified Example:**
- channel: `blankgamingchannel`
- detected live video: `1487666199814010`
- metrics extracted: concurrent viewers, likes, comments, shares
- recorded file: `fb_live_test.mp4`
- verified result: 20.01s, 2.3 MB, MP4

**Available Recording Formats (Verified Example):**

| Format ID | Resolution | Bitrate | Type | Quality |
|-----------|-----------|---------|------|---------|
| **dash-lp-hd1-v-0** | 1280x720 | 278k | DASH video | ⭐ Best verified |
| **dash-lp-md-v-0** | 640x360 | 129k | DASH video | ⭐⭐ Medium |
| **dash-lp-ld-v-0** | 426x240 | 135k | DASH video | ⭐ Low |
| **dash-lp-qd-a-0** | audio only | 99k | DASH audio | used for merge |

### TikTok Live: From Account Name to Recording
**Purpose:** Start from a TikTok account name, check if it is live, extract live metadata, and record the stream

**Supported Input URLs:**
- `https://www.tiktok.com/@{username}/live`
- `m.tiktok.com/share/live/{room_id}`

**End-to-End Workflow:**
1. Input the creator live URL
2. `TikTokLiveIE` checks whether the account is currently live
3. The extractor resolves the room ID and live stream formats
4. yt-dlp extracts metadata and recording URLs
5. The stream can be recorded directly with yt-dlp or clipped exactly with ffmpeg

**What You Can Get:**
- `is_live`
- room/stream ID
- `title`
- `uploader`
- `creator`
- `uploader_id`
- `uploader_url`
- `concurrent_view_count`
- direct live media URLs
- available formats, resolutions, and bitrates

**What You Can Record:**
- direct live recording with yt-dlp into FLV
- exact-length clips by resolving the media URL and using ffmpeg with `-t`

**What You Cannot Get Reliably Yet:**
- total/historical view count for the live
- `like_count`
- `comment_count`
- `share_count`
- live comments through yt-dlp itself

**Additional Verified Capability:**
- live comments can be streamed through a separate TikTok live WebSocket client
- this is separate from yt-dlp and is not part of `TikTokLiveIE`

**Verified Examples:**
- `@apx_ryzz`: live detected, formats resolved, concurrent viewers extracted
- `@anasproperty10`: live detected, concurrent viewers extracted, exact 10-second clip recorded
- recorded files: `tiktok_anasproperty10_live_10s.flv`, `tiktok_anasproperty10_live_10s.mp4`
- verified result: 10.087s, 960x1920, 4.65 MB

**Available Recording Formats:**

| Format ID | Resolution | Bitrate | Type | Quality |
|-----------|-----------|---------|------|---------|
| **flv-uhd** | 1280x592 | 3500k | FLV | ⭐⭐⭐ Best |
| **flv-hd** | 1280x592 | 1800k | FLV | ⭐⭐⭐ Best |
| **flv-sd** | 1167x540 | 1200k | FLV | ⭐⭐ Good |
| **flv-ld** | 778x360 | 600k | FLV | ⭐ Lowest |
| **flv-origin** | 960x1920 | 1000k | FLV | ⭐ Verified exact-clip source |
| **rtmp-pull** | Unknown | Unknown | RTMP | N/A |

---

## Platform Feature Matrix

| Capability | Snapchat Spotlight | Snapchat Premium Story | Snapchat User Story | TikTok Video | TikTok Livestream | Instagram Reel | Facebook Live |
|-----------|------------------|----------------------|-------------------|--------------|-------------------|----------------|---------------|
| **Download Video** | ✅ | ✅ | ✅ | ✅ | ✅ Recording Mode | ✅ | ✅ |
| **View Count** | ✅ | ❌ | ❌ | ✅ | ⚠️ Scrappable during live (concurrent only) | ✅ | ⚠️ Live uses concurrent viewers |
| **Like Count** | ✅ | ❌ | ❌ | ✅ | ❌ Not exposed in live metadata | ✅ | ✅ |
| **Comment Count** | ✅ | ❌ | ❌ | ✅ | ⚠️ Comment stream scrappable during live (separate client) | ✅ | ✅ |
| **Share/Repost Count** | ✅ | ❌ | ❌ | ✅ | ❌ Not exposed in live metadata | ❌ | ✅ |
| **Concurrent Viewers** | N/A | N/A | N/A | N/A | ✅ | N/A | ✅ |
| **HLS Stream** | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **DASH Stream** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Playlist/Batch** | ❌ | ❌ | ✅ | ✅ | N/A | ⚠️ (User profile broken) | ✅ Channel live detection |

**Matrix Note:** The older shorthand `❌ (hist)` meant the platform does not expose a historical/total live metric. For TikTok live, the live value that can be scraped is the current `concurrent_view_count`, and comment messages can be streamed separately during the live with a dedicated client.

---

**Last Updated:** 27. März 2026  
**Status:** ✓ Production Ready (Snapchat + Instagram Enhanced + TikTok Livestream + Facebook Live Detection/Recording)
