from collections import Counter
from app.models import Post
from app import db


def get_top_words(top_n=5, batch_size=1000):
    """Function to get the top N most frequently used words in all posts.

    Args:
        top_n (int): Number of top words to return. Default is 5.
        batch_size (int): Batch size to load data from the database. Default 1000.

    Returns:
        list[tuple[str, int]]: List of tuples ('word', number_of_uses) in descending order of frequency.
    """
    word_counter = Counter()
    offset = 0
    while True:
        posts = db.session.query(Post.body).order_by(Post.id).limit(batch_size).offset(offset).all()
        if not posts:
            break

        for post in posts:
            words = post.body.lower().split()
            word_counter.update(words)

        offset += batch_size

    return word_counter.most_common(top_n)
