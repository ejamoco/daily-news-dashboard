# Daily News Dashboard

A free GitHub Pages dashboard that summarizes the past 24 hours of news across five sections: finance, technology, biology, gaming, and China.

GitHub Actions runs every day at 00:00 UTC, which is 08:00 in Beijing time, refreshes `data/news.json`, and deploys the site.

## Files

- `index.html`: static dashboard page
- `style.css`: readable card layout and section colors
- `scripts/update_news.py`: RSS fetcher and JSON generator
- `data/news.json`: generated news data
- `.github/workflows/pages.yml`: scheduled GitHub Pages deployment

## Cost

This setup uses public GitHub Pages, GitHub Actions, public RSS feeds, and free image URLs. For this light daily usage, it is normally free.
