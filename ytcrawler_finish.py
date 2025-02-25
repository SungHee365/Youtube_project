from googleapiclient.discovery import build
import json
import re
import os
from datetime import datetime
import pytz  # KST 변환을 위해 추가

API_KEY = os.getenv("YOUTUBE_API_KEY") # 환경변수에서 API키 가져오기기

youtube = build("youtube", "v3", developerKey=API_KEY)

def get_current_time_kst():
    #기본이 UTC기준 시간이기때문에 이를 KST(한국 시간) 으로 변환하는 함수
    kst = pytz.timezone("Asia/Seoul")
    now = datetime.now(kst)
    return now.strftime("%Y-%m-%d %H:%M:%S")  # "YYYY-MM-DD HH:MM:SS" 형식

def convert_duration(iso_duration):
    #YouTube API는 ISO 8601 형식(PT4M32S)으로 길이를 제공.
    #PT 이후의 시간(H), 분(M), 초(S) 값을 정수형으로 변환.
    #예) "PT1H10M5S" -> "1:10:05"
    pattern = re.compile(r'PT(\d+H)?(\d+M)?(\d+S)?')
    matches = pattern.match(iso_duration)

    hours = int(matches.group(1)[:-1]) if matches.group(1) else 0
    minutes = int(matches.group(2)[:-1]) if matches.group(2) else 0
    seconds = int(matches.group(3)[:-1]) if matches.group(3) else 0

    return f"{hours}:{minutes:02}:{seconds:02}" if hours > 0 else f"{minutes}:{seconds:02}"



def get_video_categories(region_code="KR"):
    #YouTube API에서 카테고리 ID와 이름을 가져오는 함수
    request = youtube.videoCategories().list(
        part="snippet",
        regionCode=region_code
    )
    response = request.execute()

    category_map = {item["id"]: item["snippet"]["title"] for item in response.get("items", [])}
    return category_map




def get_trending_videos(region_code="KR", max_results=42):
    #YouTube API에서 인기급상승 동영상 정보를 가져오는 함수수
    category_map = get_video_categories(region_code)

    request = youtube.videos().list(
        part="id,snippet,contentDetails,statistics",
        chart="mostPopular",
        regionCode=region_code,
        maxResults=max_results
    )
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        category_id = item["snippet"].get("categoryId", "0")
        category_name = category_map.get(category_id, "알 수 없음")  #카테고리 이름 가져오기

        video_data = {
            "video_id": item["id"], # 영샹 고유 ID
            "title": item["snippet"]["title"], # 영상 제목
            "channel_name": item["snippet"]["channelTitle"], # 채널 이름
            "category": category_name,  # 카테고리 추가
            "duration": convert_duration(item["contentDetails"]["duration"]),  # 영상 길이
            "view_count": item["statistics"].get("viewCount", "0"), # 시청수
            "thumbnail_url": item["snippet"]["thumbnails"]["high"]["url"] # URL
        }
        videos.append(video_data)

    return videos

SAVE_DIR = "templates"
os.makedirs(SAVE_DIR, exist_ok=True)  # 폴더가 없으면 생성
SAVE_PATH = os.path.join(SAVE_DIR, "trending_videos.json")  # 최종 파일 경로

# 크롤링을 한 시간간
trending_videos = {
    "scraped_time": get_current_time_kst(),  # 크롤링한 시간을 추가
    "videos": get_trending_videos()
}

with open(SAVE_PATH, "w", encoding="utf-8") as file:
    json.dump(trending_videos, file, ensure_ascii=False, indent=4)

print(f"데이터 저장 완료: {SAVE_PATH}")
