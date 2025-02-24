from googleapiclient.discovery import build
import json
import re
import os

# YouTube API 키 가져오기
API_KEY = os.getenv("YOUTUBE_API_KEY")
# YouTube API 클라이언트 설정
youtube = build("youtube", "v3", developerKey=API_KEY)

# ISO 8601 형식의 시간을 "시간:분:초"로 변환하는 함수
def convert_duration(iso_duration):
    pattern = re.compile(r'PT(\d+H)?(\d+M)?(\d+S)?')
    matches = pattern.match(iso_duration)

    hours = int(matches.group(1)[:-1]) if matches.group(1) else 0
    minutes = int(matches.group(2)[:-1]) if matches.group(2) else 0
    seconds = int(matches.group(3)[:-1]) if matches.group(3) else 0

    return f"{hours}:{minutes:02}:{seconds:02}" if hours > 0 else f"{minutes}:{seconds:02}"

def get_best_comments(video_id, max_comments=4):
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_comments,  # 여러 개의 댓글 가져오기
            order="relevance"
        )
        response = request.execute()

        # 여러 개의 댓글을 리스트로 저장
        best_comments = [
            {
                "text": item["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
                "author": item["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                "like_count": item["snippet"]["topLevelComment"]["snippet"]["likeCount"]
            }
            for item in response.get("items", [])  # 모든 댓글 가져오기
        ]

        return best_comments  # 여러 개의 댓글 반환

    except Exception as e:
        print(f"❌ 댓글 가져오는 중 오류 발생: {e}")
        return []  # 오류 발생 시 빈 리스트 반환



#카테고리 가져오는 함수
def get_video_categories(region_code="KR"):
    request = youtube.videoCategories().list(
        part="snippet",
        regionCode=region_code
    )
    response = request.execute()

    category_map = {item["id"]: item["snippet"]["title"] for item in response.get("items", [])}
    return category_map

#  영상 가져오는 함수 (베스트 댓글 포함)
def get_trending_videos(region_code="KR", max_results=10):
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
        video_id = item["id"]
        best_comment = get_best_comments(video_id)  # 베스트 댓글 추가
        category_id = item["snippet"].get("categoryId", "0")
        category_name = category_map.get(category_id, "알 수 없음")  #카테고리 이름 가져오기

        video_data = {
            "video_id": video_id,
            "title": item["snippet"]["title"],
            "channel_name": item["snippet"]["channelTitle"],
            "category": category_name,
            "duration": convert_duration(item["contentDetails"]["duration"]),
            "view_count": item["statistics"].get("viewCount", "0"),
            "thumbnail_url": item["snippet"]["thumbnails"]["high"]["url"],
            "upload_time": item["snippet"]["publishedAt"],
            "best_comment": best_comments
        }
        videos.append(video_data)

    return videos

#  JSON 파일 저장
SAVE_DIR = "data"
os.makedirs(SAVE_DIR, exist_ok=True)
SAVE_PATH = os.path.join(SAVE_DIR, "trending_videos.json")

trending_videos = get_trending_videos()

with open(SAVE_PATH, "w", encoding="utf-8") as file:
    json.dump(trending_videos, file, ensure_ascii=False, indent=4)

print(f" 데이터 저장 완료: {SAVE_PATH}")
