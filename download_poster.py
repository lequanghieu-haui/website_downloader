import io
import os
import re
import unicodedata
from urllib.request import Request, urlopen
from PIL import Image


def normalize_title(text: str) -> str:
  """Chuyển đổi tên phim tiếng Việt thành dạng viet_thuong_khong_dau."""
  text = text.lower().replace('đ', 'd')
  text = unicodedata.normalize('NFD', text)
  text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
  text = re.sub(r'[^\w\s-]', '', text)
  return re.sub(r'[\s_]+', '_', text).strip('_')


def download_poster(
    url: str, movie_title: str, save_dir: str = '/home/quanghieu/Documents/poster'
) -> str:
  """Tải ảnh từ URL, xác minh định dạng và chuyển đổi sang JPG chuẩn."""
  os.makedirs(save_dir, exist_ok=True)

  slug = normalize_title(movie_title)
  filename = f'{slug}_poster.jpg'
  filepath = os.path.join(save_dir, filename)

  headers = {
      'User-Agent': (
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML'
          ' like Gecko) Chrome/120.0.0.0 Safari/537.36'
      ),
      'Accept': (
          'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
      ),
  }

  try:
    req = Request(url, headers=headers)
    with urlopen(req, timeout=10) as response:
      content_type = response.headers.get('Content-Type', '')

      if 'text/html' in content_type:
        print(
            '-> Loi: URL nay tra ve trang web (HTML) thay vi tep anh trực tiếp.'
        )
        print('   Mẹo: Hãy chuột phải vào ảnh trên trình duyệt -> chọn "Copy'
              ' image address" (Sao chép địa chỉ hình ảnh).')
        return ''

      image_data = response.read()

    image = Image.open(io.BytesIO(image_data))

    if image.mode in ('RGBA', 'P'):
      image = image.convert('RGB')

    image.save(filepath, 'JPEG', quality=95)
    print(f'-> Thanh cong: Da luu tai "{filepath}"')
    return filepath

  except Exception as e:
    print(f'-> Loi khi tải hoặc xử lý ảnh: {e}')
    return ''


def main():
  default_folder = '/home/quanghieu/Documents/poster'
  print('=== TOOL TAI POSTER PHIM (DA FIX LOI DINH DANG) ===')

  folder_input = (
      input(f'Nhap thư mục lưu (Enter để dùng "{default_folder}"): ')
      .strip()
      .strip('"\'')
  )
  save_dir = folder_input if folder_input else default_folder

  while True:
    try:
      print('\n' + '-' * 40)
      movie_title = input('Nhập tên phim: ').strip()
      if not movie_title:
        continue

      image_url = input('Paste link ảnh poster: ').strip()
      if not image_url:
        continue

      download_poster(image_url, movie_title, save_dir)

    except KeyboardInterrupt:
      print('\nĐã thoát chương trình.')
      break


if __name__ == '__main__':
  main()