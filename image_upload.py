import requests

def upload_to_catbox(image_path):
    url = 'https://catbox.moe/user/api.php'
    files = {'fileToUpload': open(image_path, 'rb')}
    data = {'reqtype': 'fileupload'}
    response = requests.post(url, data=data, files=files)
    if response.ok:
        return response.text.strip()
    else:
        raise Exception("Upload file error!")