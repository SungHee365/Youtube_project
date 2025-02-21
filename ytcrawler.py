from googleapiclient.discovery import build
import json
import re
import os


# YouTube API를 사용하기 위해 필요한 API_KEY를 지정합니다.
API_KEY = os.getenv("YOUTUBE_API_KEY")

# build() 함수는 Google API 클라이언트를 설정하는 부분입니다.
# youtube.v3 API 버전과 제공된 API_KEY를 사용해 클라이언트를 만듭니다.
youtube = build("youtube", "v3", developerKey=API_KEY)


# iso_duration는 ISO 8601 형식으로 된 시간 정보를 받습니다.
# 예: PT1H2M10S (1시간 2분 10초)
#이 함수는 이 형식을 "시간:분:초" 형태로 변환합니다.
#예: 1:02:10 또는 2:10 (시간이 없으면 분과 초만 출력).

def convert_duration(iso_duration):
    pattern = re.compile(r'PT(\d+H)?(\d+M)?(\d+S)?')
    matches = pattern.match(iso_duration)

    hours = int(matches.group(1)[:-1]) if matches.group(1) else 0
    minutes = int(matches.group(2)[:-1]) if matches.group(2) else 0
    seconds = int(matches.group(3)[:-1]) if matches.group(3) else 0

    return f"{hours}:{minutes:02}:{seconds:02}" if hours > 0 else f"{minutes}:{seconds:02}"



# get_trending_videos() 함수는 YouTube API를 통해 트렌딩 영상을 가져옵니다.
# 기본적으로 한국(region_code="KR")에서 인기 영상 10개(max_results=10)를 가져옵니다.
# 영상의 id, title, channelTitle, duration, viewCount, thumbnail_url 등의 정보를 수집하고,
# 이를 리스트로 반환합니다.

def get_trending_videos(region_code="KR", max_results=20):
    request = youtube.videos().list(
        part="id,snippet,contentDetails,statistics",
        chart="mostPopular",
        regionCode=region_code,
        maxResults=max_results
    )
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        video_data = {
            "video_id": item["id"],
            "title": item["snippet"]["title"],
            "channel_name": item["snippet"]["channelTitle"],
            "duration": convert_duration(item["contentDetails"]["duration"]),  # 변환된 형식 적용
            "view_count": item["statistics"].get("viewCount", "0"),
            "thumbnail_url": item["snippet"]["thumbnails"]["high"]["url"],
        }
        videos.append(video_data)

    return videos



SAVE_DIR = "data"
os.makedirs(SAVE_DIR, exist_ok=True)  # 폴더가 없으면 생성
SAVE_PATH = os.path.join(SAVE_DIR, "trending_videos.json")  # 최종 파일 경로

trending_videos = get_trending_videos()

with open(SAVE_PATH, "w", encoding="utf-8") as file:
    json.dump(trending_videos, file, ensure_ascii=False, indent=4)

print(f"데이터 저장 완료: {SAVE_PATH}")
