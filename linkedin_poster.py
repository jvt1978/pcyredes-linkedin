import requests
from linkedin_auth import get_access_token

def get_profile_urn(token: str) -> str:
    response = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    return f"urn:li:person:{response.json()['sub']}"

def _register_image_upload(token: str, author_urn: str) -> tuple:
    response = requests.post(
        "https://api.linkedin.com/v2/assets?action=registerUpload",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        },
        json={
            "registerUploadRequest": {
                "owner": author_urn,
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "serviceRelationships": [{
                    "identifier": "urn:li:userGeneratedContent",
                    "relationshipType": "OWNER"
                }],
                "supportedUploadMechanism": ["SYNCHRONOUS_UPLOAD"]
            }
        }
    )
    response.raise_for_status()
    data = response.json()["value"]
    upload_url = data["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset_urn = data["asset"]
    return upload_url, asset_urn

def _upload_image(upload_url: str, token: str, image_path: str):
    with open(image_path, "rb") as f:
        image_data = f.read()
    response = requests.put(
        upload_url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "image/jpeg"
        },
        data=image_data
    )
    response.raise_for_status()

def post_to_linkedin(text: str, image_path: str = None) -> dict:
    token = get_access_token()
    author_urn = get_profile_urn(token)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    if image_path:
        upload_url, asset_urn = _register_image_upload(token, author_urn)
        _upload_image(upload_url, token, image_path)

        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "IMAGE",
                    "media": [{
                        "status": "READY",
                        "media": asset_urn,
                        "title": {"text": text[:100]}
                    }]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
    else:
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

    response = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()
