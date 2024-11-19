from collections import defaultdict

from atproto import models

from server.logger import logger
from server.database import db, Post


KEYWORDS = {
    "publichealth",
    "vaccine",
    "vaccines",
    "vaccination",
    "mrna",
    "booster"
}

import os
import openai

# Initialize OpenAI client
from dotenv import load_dotenv
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def detect_vaccine_denialism(text: str) -> bool:
    """
    Uses OpenAI's API to determine if a post contains vaccine denialism.
    Returns True if vaccine denialism is detected, False otherwise.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at detecting vaccine misinformation and denialism. Respond with only 'true' if the text contains vaccine denialism or 'false' if it does not."},
                {"role": "user", "content": text}
            ],
            temperature=0,
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip().lower()
        print("!!!!!RESULT", result)
        return result == "true"
        
    except Exception as e:
        logger.error(f"Error detecting vaccine denialism: {e}")
        return False




def operations_callback(ops: defaultdict) -> None:
    # Here we can filter, process, run ML classification, etc.
    # After our feed alg we can save posts into our DB
    # Also, we should process deleted posts to remove them from our DB and keep it in sync

    # for example, let's create our custom feed that will contain all posts that contains alf related text

    posts_to_create = []
    for created_post in ops[models.ids.AppBskyFeedPost]['created']:
        author = created_post['author']
        record = created_post['record']

        # print all texts just as demo that data stream works
        # post_with_images = isinstance(record.embed, models.AppBskyEmbedImages.Main)
        # inlined_text = record.text.replace('\n', ' ')
        # logger.info(
        #     f'NEW POST '
        #     f'[CREATED_AT={record.created_at}]'
        #     f'[AUTHOR={author}]'
        #     f'[WITH_IMAGE={post_with_images}]'
        #     f': {inlined_text}'
        # )


        # if author in ALLOWED_AUTHORS:

        if any(keyword in record.text.lower() for keyword in KEYWORDS):
            contains_denialism = detect_vaccine_denialism(record.text)
            if not contains_denialism:
                post_with_images = isinstance(record.embed, models.AppBskyEmbedImages.Main)
                inlined_text = record.text.replace('\n', ' ')
                logger.info(
                    f'NEW POST '
                    f'[CREATED_AT={record.created_at}]'
                f'[AUTHOR={author}]'
                    f'[WITH_IMAGE={post_with_images}]'
                f': {inlined_text}'
                )
                reply_root = reply_parent = None
                if record.reply:
                    reply_root = record.reply.root.uri
                    reply_parent = record.reply.parent.uri

                post_dict = {
                    'uri': created_post['uri'],
                    'cid': created_post['cid'],
                    'reply_parent': reply_parent,
                    'reply_root': reply_root,
                }
                posts_to_create.append(post_dict)

    posts_to_delete = ops[models.ids.AppBskyFeedPost]['deleted']
    if posts_to_delete:
        post_uris_to_delete = [post['uri'] for post in posts_to_delete]
        Post.delete().where(Post.uri.in_(post_uris_to_delete))
        # logger.info(f'Deleted from feed: {len(post_uris_to_delete)}')

    if posts_to_create:
        with db.atomic():
            for post_dict in posts_to_create:
                Post.create(**post_dict)
        logger.info(f'Added to feed: {len(posts_to_create)}')
