from google_images_download import google_images_download

def download_images(**args):
    downloader = google_images_download.googleimagesdownload()
    result = downloader.download(args)
    
download_images(single_image='https://photos.google.com/photo/AF1QipMD5bG5zCiaTXdZ6aIYb7cWZpEwYW-SlPhkSVDq')    
download_images(url='https://photos.google.com/share/AF1QipMQP1VtB--wgI04pL9maVyRY1rvKIi794F9XulN7J23yv9w4F7iYJ1gBA0fgk1gfw?key=bC1fMjF2NEpwSVYtRmxRMTFfRmdOTG1uLWxrdzh3')    
