import os
import requests
import logging

def make_video(article):
    """
    Mock Media Generator: Returns a vertical 9:16 video URL.
    In a real implementation, this would use an API like Shotstack or Creatomate.
    """
    # Using a placeholder vertical video for demonstration
    video_url = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4"
    logging.info(f"Generated video for article: {article['id']}")
    return video_url

def make_image(article):
    """
    Mock Media Generator: Returns a 1080x1080 image URL with branding.
    """
    # Using Unsplash source with keywords for relevance
    image_id = abs(hash(article['title'])) % 1000
    image_url = f"https://images.unsplash.com/photo-{1550751827 + image_id}?auto=format&fit=crop&q=80&w=1080&h=1080"
    logging.info(f"Generated image for article: {article['id']}")
    return image_url
