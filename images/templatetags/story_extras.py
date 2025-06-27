import json
from django import template

register = template.Library()


@register.filter
def story_image_list_json(stories):
    image_urls = []
    for story in stories:
        for img in story.images.all():
            image_urls.append(img.image.url)
    return json.dumps(image_urls)
