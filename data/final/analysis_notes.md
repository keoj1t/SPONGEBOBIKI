# Playbook Analysis Notes

## 1. Dataset Overview
- How many content types are there and which one dominates?
  There are 6 content types: post (650), video (480), tweet (295), thread (295), carousel_album (100), reel (74). Posts dominate in count, but videos dominate in engagement with avg 5,288 on YouTube alone.
- Which platforms are included? Reddit, YouTube, TikTok, Twitter (X), Instagram, LinkedIn, Threads — 7 platforms total.
- How much data per platform? The dataset is balanced at ~300 rows per platform:
  - Reddit: 298 rows
  - Twitter: 295 rows
  - Threads: 295 rows
  - LinkedIn: 284 rows
  - TikTok: 257 rows
  - Instagram: 242 rows
  - YouTube: 223 rows
- Total rows: 1,894 after deduplication and English-only filtering.
- What fields are commonly missing? Views are only tracked for YouTube and TikTok. LinkedIn engagement data is zero (scraper limitation — no cookies). Reddit and Twitter have partial view data.
- How evenly distributed is the data across platforms? Very even — each platform contributes 12–16% of the dataset. This allows fair cross-platform comparisons.

## 2. CROSS-PLATFORM ANALYSIS
- Which platform has the highest average engagement?
  Instagram leads with avg 18,144 (driven by viral reels), followed by TikTok at 10,079 and YouTube at 5,288. These three visual platforms vastly outperform text-heavy ones.
- Which platform has the most posts? Reddit (298), closely followed by Twitter and Threads (295 each). The dataset is balanced.
- Where is engagement high but post count low? Instagram punches above its weight — only 242 posts but 18K avg engagement. TikTok is similar: 257 posts, 10K avg.
- Where are there lots of posts but low engagement? LinkedIn (284 posts, 0 avg engagement — scraper limitation) and Threads (295 posts, 463 avg engagement). Twitter is middling at 529 avg.
- How do conversations about Claude differ across platforms?

  Reddit — deep technical discussions, model comparisons, debugging stories, pricing complaints. Median engagement 434.

  YouTube — tutorials, full courses, comparison videos ("ChatGPT vs Claude"). Highest individual post engagement (190K). Content is educational + entertainment.

  TikTok — short viral videos, quick demos, "wow-effect" content. Very high engagement per post (10K avg), driven by views.

  Twitter — news drops, hot takes, opinion threads. Quick reactions to updates and announcements. Median engagement only 24.

  Instagram — visual-first: carousel posts, reels, memes. Viral potential is massive (top post: 1.3M engagement) but inconsistent.

  LinkedIn — professional write-ups, enterprise use cases. No engagement data available in this scrape (API limitation).

  Threads — emerging platform. Mix of tips, viral lists, news commentary. Lower engagement (avg 463, median 73) but growing.

## 3. TOP PERFORMING CONTENT
What are the top 5 posts by engagement?
1. "We asked every AI the same question" (Instagram, 1.33M) — AI moral dilemma comparison
2. "This is so goated" (Instagram, 861K) — viral reaction + AI comparison
3. "We asked 5 AI systems who should be sacrificed" (Instagram, 722K) — ethical test across AI models
4. "It's time to switch from ChatGPT" (TikTok, 415K) — direct switching call
5. "Claude aura farming" (TikTok, 299K) — meme-style AI comparison

What do they have in common?
- 3 out of 5 are Instagram, 2 are TikTok. Visual platforms dominate the top.
- Every top post involves a comparison or competition between AI models.
- Emotional/provocative framing: ethical dilemmas, switching narratives, "wow" reactions.
- None are from official Anthropic channels — all user-generated content.

Comparisons (vs ChatGPT)? All 5 top posts are comparisons. The competitive narrative ("Claude vs ChatGPT vs Gemini") is the #1 engagement driver across all platforms.

Switching narratives? Yes — post #4 is a direct "switch from ChatGPT" call (415K engagement). The switching narrative appears in 97 posts with avg 3,084 engagement.

Numbers (ROI, time)? Present in broader dataset: "$195K → $33K hospital bill," "4 hours full course," "10x faster." Concrete numbers consistently boost engagement.

Emotional or rational? Overwhelmingly emotional. The top performers use shock, moral dilemmas, and meme energy. Even technical content that goes viral is wrapped in emotional framing.

## 4. CONTENT TYPE ANALYSIS
Which content type drives the best engagement?
- carousel_album: avg 28,682 (Instagram), strong visual storytelling
- video: avg 5,288 (YouTube) / avg 10,079 (TikTok), high reach through tutorials and reviews
- reel: avg 6,100 (Instagram), works when paired with trending audio
- post: avg 1,055 (Reddit), solid for in-depth discussions
- tweet: avg 529 (Twitter), best for news and quick takes
- thread: avg 463 (Threads), emerging format

Video and visual formats dominate. Text-only formats underperform by 5-10x.

## 5. KEYWORD ANALYSIS
- What are the most common keywords?
  - code: 624 mentions
  - gpt: 541
  - chatgpt: 453
  - coding: 304
  - vs: 245
  - api: 200
  - better: 192
  - switch: 120
  - compare: 41

- Claude is primarily discussed in the context of coding (code + coding = 928 mentions) and competition with ChatGPT (chatgpt + gpt + vs = 1,239 mentions).

- The "switch" keyword (120 mentions) appears in high-engagement posts, confirming that switching narratives drive strong reactions.

## 6. NARRATIVE ANALYSIS
- What are the most common narrative buckets?
  - coding_dev: 769 posts (40.6%), avg engagement 2,337
  - comparison: 593 posts (31.3%), avg engagement 6,902
  - education_tutorial: 384 posts (20.3%), avg engagement 4,246
  - productivity_roi: 384 posts (20.3%), avg engagement 6,957
  - trust_safety: 123 posts (6.5%), avg engagement 2,088
  - switching: 97 posts (5.1%), avg engagement 3,084

- Which generate the highest total engagement?
  1. comparison: 4,092,642 total — the dominant narrative by total impact
  2. productivity_roi: 2,671,550 total
  3. coding_dev: 1,797,218 total
  4. education_tutorial: 1,630,640 total
  5. switching: 299,128 total
  6. trust_safety: 256,879 total

- The comparison narrative is the clear engagement leader, both per-post and in aggregate. People love "X vs Y" content.

## 7. GROWTH MECHANICS
- How do users learn about Claude?
  Primarily through user-generated content on Reddit (discussion), YouTube (tutorials), and TikTok/Instagram (viral clips). No evidence of paid advertising in the top-performing content.

- Are there signs of organic growth?
  Yes — strong signals:
  - All top posts are user-generated, not brand content
  - Switching narratives (97 posts) show users actively choosing Claude over competitors
  - Coding community adoption (769 coding/dev posts) shows real developer traction
  - Cross-platform presence across 7 platforms without paid promotion

- Are there any signs of engineered growth?
  Minimal. Trust/safety (123 posts, lowest engagement) would be stronger if there was a marketing push. LinkedIn presence exists but has no engagement data. The comparison narrative may be partially fueled by the competitive market rather than orchestrated campaigns.

## 8. DISTRIBUTION PATTERNS
- Who spreads the content? Almost entirely users. Among the top viral posts, no official Anthropic content appears. The community creates and distributes Claude content independently.

- Which formats spread best? Visual content dominates: Instagram carousels (avg 28K), TikTok videos (avg 10K), YouTube tutorials (avg 5K). Short-form video is king for virality.

- Which posts spark discussions? Conflict-driven and ethical content generates the most comments. AI comparison posts, switching narratives, and real-world use cases (hospital bill, coding challenges) drive discussion.

## 9. WHAT DRIVES ENGAGEMENT
- Comparisons are the #1 driver. "vs" posts average 6,902 engagement — 3x the dataset average.
- Visual formats (video, carousel, reel) outperform text by 5-10x.
- Concrete numbers and real-world outcomes boost engagement significantly.
- Emotional framing (shock, moral dilemmas, "I was wrong about Claude") multiplies reach.

## 10. WHAT DOES NOT WORK
- LinkedIn posts show near-zero engagement in this dataset.
- Trust/safety narrative (123 posts) has the lowest avg engagement at 2,088.
- Generic "AI is the future" posts without specifics consistently underperform.
- Text-only formats on visual platforms (Instagram text posts, Twitter threads without media) get minimal traction.

## 11. UNEXPECTED FINDINGS
- Instagram dominates the top 5 by engagement — a platform often overlooked for AI content.
- Threads (Meta's new platform) already has significant Claude discussion (295 posts), suggesting early adoption by the AI community.
- The "Claude" gaming character (Mobile Legends) still causes data noise — posts about the MLBB hero appear in YouTube results.
- TikTok has surprisingly high per-post engagement (10K avg) for AI content, contradicting assumptions that AI topics don't work on short-video platforms.
