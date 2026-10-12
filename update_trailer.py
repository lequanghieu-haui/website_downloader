import re
from supabase import Client, create_client

# ==========================================
# CẤU HÌNH THÔNG TIN SUPABASE
# ==========================================
SUPABASE_URL = "https://plbxrtlksugbpttgmyux.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBsYnhydGxrc3VnYnB0dGdteXV4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MDE2OTIyNywiZXhwIjoyMTA1NzQ1MjI3fQ.kXgpTgGS-TkuoEBO6-VctVZOgcU3rwTRAGfpb4vCKdc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def clean_youtube_url(url: str) -> str:
  """Chuyển đổi URL YouTube bất kỳ về dạng Embed chuẩn để nhúng iframe."""
  url = url.strip()
  match = re.search(
      r'(?:v=|\/embed\/|\/v\/|youtu\.be\/)([a-zA-Z0-9_-]{11})', url
  )
  if match:
    video_id = match.group(1)
    return f'https://www.youtube.com/embed/{video_id}'
  return url


def get_movie_by_id(movie_id: int) -> dict | None:
  """Kiểm tra và lấy thông tin phim theo movie_id."""
  try:
    response = (
        supabase.table("movies")
        .select("movie_id, title, trailer_url")
        .eq("movie_id", movie_id)
        .execute()
    )

    if response.data and len(response.data) > 0:
      return response.data[0]
    else:
      print(f"Loi: Khong tim thay phim trong CSDL voi movie_id = {movie_id}")
      return None
  except Exception as e:
    print(f"Loi khi truy van CSDL: {e}")
    return None


def update_trailer_url(movie_id: int, youtube_url: str) -> bool:
  """Cập nhật cột trailer_url trong bảng public.movies."""
  try:
    response = (
        supabase.table("movies")
        .update({"trailer_url": youtube_url})
        .eq("movie_id", movie_id)
        .execute()
    )

    if response.data:
      return True
    else:
      print(f"Khong the cap nhat CSDL cho movie_id = {movie_id}.")
      return False
  except Exception as e:
    print(f"Loi khi cap nhat trailer_url: {e}")
    return False


def process_update_trailer(movie_id_input: str, raw_youtube_url: str):
  """Quy trình cập nhật trailer."""
  print("\n--- BAT DAU CAP NHAT TRAILER ---")

  try:
    movie_id = int(movie_id_input)
  except ValueError:
    print("Loi: movie_id phai la mot so nguyen!")
    return

  # 1. Tra cứu thông tin phim
  movie = get_movie_by_id(movie_id)
  if not movie:
    return

  title = movie.get("title")
  old_trailer = movie.get("trailer_url") or "(Chua co)"
  print(f"-> Phim duoc chon: [ID: {movie_id}] - Ten: '{title}'")
  print(f"-> Trailer hien tai: {old_trailer}")

  # 2. Làm sạch link YouTube
  cleaned_url = clean_youtube_url(raw_youtube_url)
  print(f"-> Trailer moi: {cleaned_url}")

  # 3. Cập nhật vào CSDL
  if update_trailer_url(movie_id, cleaned_url):
    print(f"-> Thanh cong: Da cap nhat trailer_url cho phim '{title}'.")

  print("--- HOAN THANH ---")


def main():
  print("=== TOOL CAP NHAT TRAILER YOUTUBE HO CHO MOVIE ===")

  while True:
    try:
      print("\n" + "-" * 40)
      movie_id_input = input("Nhap movie_id (so nguyen): ").strip()
      if not movie_id_input:
        print("movie_id khong duoc de trong!")
        continue

      youtube_url = input("Paste link YouTube trailer: ").strip()
      if not youtube_url:
        print("Link YouTube khong duoc de trong!")
        continue

      process_update_trailer(movie_id_input, youtube_url)

    except KeyboardInterrupt:
      print("\nDa thoat chuong trinh.")
      break


if __name__ == "__main__":
  main()