import requests
from colorama import Fore # Keep for potential future logging

def parse_cookie_string(cookie_str: str) -> dict:
    cookies = {}
    for part in cookie_str.split('; '):
        if '=' in part:
            k, v = part.split('=', 1)
            cookies[k.strip()] = v.strip()
    return cookies

def shortcode_to_media_id(shortcode: str) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    media_id = 0
    for c in shortcode:
        media_id = media_id * 64 + alphabet.index(c)
    return str(media_id)

def follow_user(username: str, cookie_str: str) -> bool:
    cookies = parse_cookie_string(cookie_str)
    headers = {
        'User-Agent': 'Mozilla/5.0', 'X-IG-App-ID': '936619743392459',
        'X-CSRFToken': cookies.get('csrftoken', ''), 'Referer': f'https://www.instagram.com/{username}/'
    }
    try:
        profile_res = requests.get(f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}', headers=headers, cookies=cookies)
        if profile_res.status_code != 200: return False
        user_id = profile_res.json()['data']['user']['id']
        follow_res = requests.post(f"https://www.instagram.com/api/v1/friendships/create/{user_id}/", headers=headers, cookies=cookies)
        return follow_res.status_code == 200
    except Exception:
        return False

def like_post(post_url: str, cookie_str: str) -> bool:
    cookies = parse_cookie_string(cookie_str)
    headers = {'User-Agent': 'Mozilla/5.0', 'X-CSRFToken': cookies.get('csrftoken', '')}
    try:
        shortcode = post_url.split("/p/")[1].split("/")[0]
        media_id = shortcode_to_media_id(shortcode)
        like_url = f"https://www.instagram.com/web/likes/{media_id}/like/"
        like_res = requests.post(like_url, headers=headers, cookies=cookies)
        return like_res.status_code == 200
    except Exception:
        return False

def comment_post(post_url: str, comment_text: str, cookie_str: str) -> bool:
    cookies = parse_cookie_string(cookie_str)
    headers = {'User-Agent': 'Mozilla/5.0', 'X-CSRFToken': cookies.get('csrftoken', '')}
    try:
        shortcode = post_url.split("/p/")[1].split("/")[0]
        media_id = shortcode_to_media_id(shortcode)
        comment_url = f"https://www.instagram.com/web/comments/{media_id}/add/"
        payload = {"comment_text": comment_text}
        comment_res = requests.post(comment_url, headers=headers, cookies=cookies, data=payload)
        return comment_res.status_code == 200
    except Exception:
        return False

def get_instagram_profile_info(username: str, cookie_str: str) -> dict:
    cookies = parse_cookie_string(cookie_str)
    headers = {'User-Agent': 'Mozilla/5.0', 'X-IG-App-ID': '936619743392459'}
    try:
        response = requests.get(f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}", headers=headers, cookies=cookies)
        if response.status_code == 200:
            return response.json()['data']['user']
        return None
    except Exception:
        return None
