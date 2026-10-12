import io
import os
import re
import unicodedata
from urllib.request import Request, urlopen
from PIL import Image
from supabase import Client, create_client

# ==========================================
# CẤU HÌNH THÔNG TIN SUPABASE
# ==========================================
SUPABASE_URL = "https://plbxrtlksugbpttgmyux.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBsYnhydGxrc3VnYnB0dGdteXV4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MDE2OTIyNywiZXhwIjoyMTA1NzQ1MjI3fQ.kXgpTgGS-TkuoEBO6-VctVZOgcU3rwTRAGfpb4vCKdc"
BUCKET_NAME = "poster"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def normalize_title(text: str) -> str:
  """Chuyển đổi tên phim tiếng Việt thành dạng viet_thuong_khong_dau."""
  text = text.lower().replace("đ", "d")
  text = unicodedata.normalize("NFD", text)
  text = "".join(char for char in text if unicodedata.category(char) != "Mn")
  text = re.sub(r"[^\w\s-]", "", text)
  return re.sub(r"[\s_]+", "_", text).strip("_")


def get_movie_info_by_id(movie_id: int) -> tuple[int, str] | None:
  """Truy vấn lấy thông tin title dựa trên movie_id."""
  try:
    response = (
        supabase.table("movies")
        .select("movie_id, title")
        .eq("movie_id", movie_id)
        .execute()
    )

    if response.data and len(response.data) > 0:
      movie_data = response.data[0]
      return movie_data["movie_id"], movie_data["title"]
    else:
      print(f"Loi: Khong tim thay phim trong CSDL voi movie_id = {movie_id}")
      return None
  except Exception as e:
    print(f"Loi khi truy van CSDL: {e}")
    return None


def download_and_process_image(url: str) -> bytes | None:
  """Tải ảnh từ URL và chuyển đổi về dữ liệu JPEG chuẩn."""
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept": (
          "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
      ),
  }

  try:
    req = Request(url, headers=headers)
    with urlopen(req, timeout=10) as response:
      content_type = response.headers.get("Content-Type", "")
      if "text/html" in content_type:
        print("Loi: URL tra ve trang web HTML thay vi tep anh truc tiep.")
        return None
      image_data = response.read()

    image = Image.open(io.BytesIO(image_data))
    if image.mode in ("RGBA", "P"):
      image = image.convert("RGB")

    output_buffer = io.BytesIO()
    image.save(output_buffer, format="JPEG", quality=95)
    return output_buffer.getvalue()

  except Exception as e:
    print(f"Loi khi tai hoac xu ly anh: {e}")
    return None


def upload_to_supabase_storage(image_bytes: bytes, file_name: str) -> str | None:
  """Tải dữ liệu ảnh lên Supabase Storage và trả về Public URL."""
  try:
    supabase.storage.from_(BUCKET_NAME).upload(
        path=file_name,
        file=image_bytes,
        file_options={"content-type": "image/jpeg", "upsert": "true"},
    )

    public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_name)
    print(f"Da upload file '{file_name}' len Storage: {public_url}")
    return public_url

  except Exception as e:
    print(f"Loi khi upload len Supabase Storage: {e}")
    return None


def update_movie_poster_url(movie_id: int, public_url: str) -> bool:
  """Cập nhật cột poster_url trong bảng public.movies theo movie_id."""
  try:
    response = (
        supabase.table("movies")
        .update({"poster_url": public_url})
        .eq("movie_id", movie_id)
        .execute()
    )

    if response.data:
      print(f"Da cap nhat poster_url thanh cong cho movie_id = {movie_id}.")
      return True
    else:
      print(f"Khong the cap nhat CSDL cho movie_id = {movie_id}.")
      return False

  except Exception as e:
    print(f"Loi khi cap nhat CSDL Supabase: {e}")
    return False


def process_poster_workflow(image_url: str, movie_id_input: str):
  """Quy trình tự động đầy đủ."""
  print("\n--- BAT DAU QUY TRINH TU DONG ---")

  try:
    movie_id = int(movie_id_input)
  except ValueError:
    print("Loi: movie_id phai la mot so nguyen!")
    return

  # 1. Lấy thông tin phim từ CSDL theo ID
  print("1. Dang tim thong tin phim trong CSDL...")
  movie_info = get_movie_info_by_id(movie_id)
  if not movie_info:
    print("Quy trinh That bai tai Buoc 1 (Khong tim thay ID).")
    return

  _, title = movie_info
  print(f"-> Da tim thay phim: [ID: {movie_id}] - Ten: '{title}'")

  # 2. Tạo tên file chuẩn: id_ten_phim_poster.jpg
  slug = normalize_title(title)
  file_name = f"{movie_id}_{slug}_poster.jpg"
  print(f"-> Quy cach ten file: '{file_name}'")

  # 3. Tải và xử lý ảnh
  print("2. Dang tai va kiem tra anh...")
  image_bytes = download_and_process_image(image_url)
  if not image_bytes:
    print("Quy trinh That bai tai Buoc 2 (Loi anh).")
    return

  # 4. Upload lên Supabase Storage
  print("3. Dang day anh len Supabase Storage...")
  public_url = upload_to_supabase_storage(image_bytes, file_name)
  if not public_url:
    print("Quy trinh That bai tai Buoc 3 (Loi upload).")
    return

  # 5. Cập nhật URL vào bảng movies
  print("4. Dang cap nhat poster_url vao bang movies...")
  update_movie_poster_url(movie_id, public_url)

  print("--- HOAN THANH QUY TRINH ---\n")


def main():
  print("=== TOOL UPLOAD POSTER PHIM (MAC DINH THEO MOVIE ID) ===")

  while True:
    try:
      print("\n" + "-" * 40)
      movie_id_input = input("Nhap movie_id (so nguyen): ").strip()
      if not movie_id_input:
        print("movie_id khong duoc de trong!")
        continue

      image_url = input("Paste link anh poster: ").strip()
      if not image_url:
        print("Link anh khong duoc de trong!")
        continue

      process_poster_workflow(image_url, movie_id_input)

    except KeyboardInterrupt:
      print("\nDa thoat chuong trinh.")
      break


if __name__ == "__main__":
  main()