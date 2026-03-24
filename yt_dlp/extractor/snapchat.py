from .common import InfoExtractor
from ..utils import float_or_none, int_or_none, url_or_none
from ..utils.traversal import traverse_obj


class SnapchatUserStoryIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?snapchat\.com/@(?P<id>[\w.]+)(?:/story)?'

    _TESTS = [{
        'url': 'https://www.snapchat.com/@anna-strigl/story',
        'info_dict': {
            'id': 'anna-strigl',
            '_type': 'playlist',
            'uploader': 'Anna Strigl',
            'uploader_id': 'anna-strigl',
        },
        'playlist_count': 14,
    }]

    def _real_extract(self, url):
        username = self._match_id(url)
        webpage = self._download_webpage(url, username)
        page_props = self._search_nextjs_data(webpage, username)['props']['pageProps']

        story = page_props.get('story', {})
        profile_info = traverse_obj(page_props, ('userProfile', 'publicProfileInfo'), {})
        snaps = story.get('snapList', [])

        entries = []
        for snap_index, snap in enumerate(snaps, 1):
            snap_id = traverse_obj(snap, ('snapId', 'value', {str})) or f'{username}_{snap_index}'
            media_type = snap.get('snapMediaType', 1)  # 1=PHOTO, 2=VIDEO
            timestamp = traverse_obj(snap, ('timestampInSec', 'value', {int_or_none}))
            snap_urls = snap.get('snapUrls', {})
            media_url = snap_urls.get('mediaUrl', '')

            entry = {
                'id': snap_id,
                'title': f'Story {snap_index}',
                'uploader': profile_info.get('title'),
                'uploader_id': profile_info.get('mutableName'),
                'timestamp': timestamp,
                'channel_follower_count': traverse_obj(profile_info, ('subscriberCount', {int_or_none})),
            }

            # User stories deliver videos via mediaUrl (even though path says /i/)
            # Always try mediaUrl first - it's either MP4 video or image
            if media_url:
                entry['url'] = media_url
                # Default to mp4 for user stories (they're typically videos)
                entry['ext'] = 'mp4'
            
            # Fallback: if there's an HLS videoTrackUrl, prefer that
            if media_type == 2 and 'videoTrackUrl' in snap_urls:
                video_url = snap_urls['videoTrackUrl']
                formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                    video_url, snap_id, 'mp4', m3u8_id='hls', fatal=False)
                entry.update({
                    'url': video_url,
                    'formats': formats,
                    'subtitles': subtitles,
                })

            entries.append(entry)

        return {
            '_type': 'playlist',
            'id': username,
            'title': f'{profile_info.get("title")} Story',
            'uploader': profile_info.get('title'),
            'uploader_id': profile_info.get('mutableName'),
            'channel_follower_count': traverse_obj(profile_info, ('subscriberCount', {int_or_none})),
            'entries': entries,
        }


class SnapchatStoryIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?snapchat\.com/p/(?P<profile_id>[\w-]+)/(?P<id>\d+)'

    _TESTS = [{
        'url': 'https://www.snapchat.com/p/d7c05957-737e-4846-9a7d-9324ea237474/760052191735808',
        'info_dict': {
            'id': '760052191735808',
            'ext': 'mp4',
            'title': str,
            'thumbnail': r're:https://cf-st\.sc-cdn\.net/',
            'uploader': str,
        },
    }, {
        'url': 'https://www.snapchat.com/p/d7c05957-737e-4846-9a7d-9324ea237474/3137372758437888',
        'info_dict': {
            'id': '3137372758437888',
            'ext': 'mp4',
            'title': str,
            'thumbnail': r're:https://cf-st\.sc-cdn\.net/',
            'uploader': str,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        page_props = self._search_nextjs_data(webpage, video_id)['props']['pageProps']

        story_data = traverse_obj(page_props, ('preselectedStory', 'premiumStory'))
        player_story = traverse_obj(story_data, 'playerStory')

        # Find the first snap with a media URL
        m3u8_url = traverse_obj(player_story, (
            'snapList', lambda _, v: v['snapUrls']['mediaUrl'],
            'snapUrls', 'mediaUrl', any))

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            m3u8_url, video_id, 'mp4', m3u8_id='hls', fatal=False)

        thumbnail = traverse_obj(player_story, (
            'snapList', 0, 'snapUrls', 'mediaPreviewUrl', 'value', {url_or_none}))
        if not thumbnail:
            thumbnail = traverse_obj(player_story, ('thumbnailUrl', 'value', {url_or_none}))

        return {
            'id': video_id,
            'title': traverse_obj(player_story, ('storyTitle', 'value', {str})),
            'thumbnail': thumbnail,
            'formats': formats,
            'subtitles': subtitles,
            'uploader': traverse_obj(page_props, ('publicProfileInfo', 'title', {str})),
            'uploader_id': traverse_obj(page_props, ('publicProfileInfo', 'mutableName', {str})),
            'timestamp': traverse_obj(page_props, (
                'preselectedStory', 'timestampInSec', 'value', {int_or_none})),
            'channel_follower_count': traverse_obj(page_props, (
                'publicProfileInfo', 'subscriberCount', {int_or_none})),
        }


class SnapchatSpotlightIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?snapchat\.com/(?:@[\w.]+/)?spotlight/(?P<id>[\w-]+)'

    _TESTS = [{
        'url': 'https://www.snapchat.com/spotlight/W7_EDlXWTBiXAEEniNoMPwAAYYWtidGhudGZpAX1TKn0JAX1TKnXJAAAAAA',
        'md5': '46c580f63592d0cbb76e974d2f9f0fcc',
        'info_dict': {
            'id': 'W7_EDlXWTBiXAEEniNoMPwAAYYWtidGhudGZpAX1TKn0JAX1TKnXJAAAAAA',
            'ext': 'mp4',
            'title': 'Views 💕',
            'description': '',
            'thumbnail': r're:https://cf-st\.sc-cdn\.net/d/kKJHIR1QAznRKK9jgYYDq\.256\.IRZXSOY',
            'duration': 4.665,
            'timestamp': 1637777831.369,
            'upload_date': '20211124',
            'repost_count': int,
            'uploader': 'shreypatel57',
            'uploader_url': 'https://www.snapchat.com/add/shreypatel57',
        },
    }, {
        'url': 'https://www.snapchat.com/spotlight/W7_EDlXWTBiXAEEniNoMPwAAYcnVjYWdwcGV1AZEaIYn5AZEaIYnrAAAAAQ',
        'md5': '4cd9626458c1a0e3e6dbe72c544a9ec2',
        'info_dict': {
            'id': 'W7_EDlXWTBiXAEEniNoMPwAAYcnVjYWdwcGV1AZEaIYn5AZEaIYnrAAAAAQ',
            'ext': 'mp4',
            'title': 'Spotlight Snap',
            'description': 'How he flirt her teacher🤭🤭🤩😍 #kdrama#cdrama #dramaclips #dramaspotlight',
            'thumbnail': r're:https://cf-st\.sc-cdn\.net/i/ztfr6xFs0FOcFhwVczWfj\.256\.IRZXSOY',
            'duration': 10.91,
            'timestamp': 1722720291.307,
            'upload_date': '20240803',
            'view_count': int,
            'repost_count': int,
            'uploader': 'ganda0535',
            'uploader_url': 'https://www.snapchat.com/add/ganda0535',
            'tags': ['#dramaspotlight', '#dramaclips', '#cdrama', '#kdrama'],
        },
    }, {
        'url': 'https://www.snapchat.com/@isajjad91/spotlight/W7_EDlXWTBiXAEEniNoMPwAAYcnRheXVpbHJzAZyv3Wz-AZyv3WsQAAAAAw',
        'info_dict': {
            'id': 'W7_EDlXWTBiXAEEniNoMPwAAYcnRheXVpbHJzAZyv3Wz-AZyv3WsQAAAAAw',
            'ext': 'mp4',
            'title': 'Spotlight Snap',
            'description': 'Another Spotlight Snap brought to you by Snapchat',
            'timestamp': 1772477049.616,
            'upload_date': '20260302',
            'view_count': int,
            'repost_count': int,
            'comment_count': int,
            'like_count': int,
            'uploader': 'isajjad91',
            'uploader_url': 'https://www.snapchat.com/@isajjad91',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        page_props = self._search_nextjs_data(webpage, video_id)['props']['pageProps']
        video_data = traverse_obj(page_props, (
            'spotlightFeed', 'spotlightStories',
            lambda _, v: traverse_obj(v, ('story', 'storyId', 'value')) == video_id, 'metadata', any), None)

        return {
            'id': video_id,
            'ext': 'mp4',
            **traverse_obj(video_data, ('videoMetadata', {
                'title': ('name', {str}),
                'description': ('description', {str}),
                'timestamp': ('uploadDateMs', {float_or_none(scale=1000)}),
                'view_count': ('viewCount', {int_or_none}, {lambda x: None if x == -1 else x}),
                'repost_count': ('shareCount', {int_or_none}),
                'url': ('contentUrl', {url_or_none}),
                'width': ('width', {int_or_none}),
                'height': ('height', {int_or_none}),
                'duration': ('durationMs', {float_or_none(scale=1000)}),
                'thumbnail': ('thumbnailUrl', {url_or_none}),
                'uploader': ('creator', 'personCreator', 'username', {str}),
                'uploader_url': ('creator', 'personCreator', 'url', {url_or_none}),
            })),
            **traverse_obj(video_data, {
                'description': ('description', {str}),
                'tags': ('hashtags', ..., {str}),
                'view_count': ('engagementStats', 'viewCount', {int_or_none}, {lambda x: None if x == -1 else x}),
                'repost_count': ('engagementStats', 'shareCount', {int_or_none}),
                'comment_count': ('engagementStats', 'commentCount', {int_or_none}),
                'like_count': ('engagementStats', 'boostCount', {int_or_none}),
            }),
        }
