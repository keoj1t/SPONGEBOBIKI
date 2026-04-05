"""Free web search — DuckDuckGo, Bing, Google fallback chain. No API keys."""

import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse, parse_qs, unquote

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


def _new_session():
    s = requests.Session()
    s.headers.update({
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
    })
    return s


_session = _new_session()
_ddg_broken = False


def _headers():
    return {"User-Agent": random.choice(UA_LIST)}


def _retry_request(method, url, max_retries=2, **kwargs):
    global _session
    kwargs.setdefault("timeout", 12)
    kwargs.setdefault("headers", _headers())

    for attempt in range(max_retries):
        try:
            if method == "POST":
                resp = _session.post(url, **kwargs)
            else:
                resp = _session.get(url, **kwargs)
            if resp.status_code in (429, 503):
                wait = (attempt + 1) * 2 + random.uniform(0.5, 1.5)
                time.sleep(wait)
                _session = _new_session()
                continue
            return resp
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt < max_retries - 1:
                wait = (attempt + 1) * 2 + random.uniform(0.5, 1.5)
                time.sleep(wait)
                _session = _new_session()
            else:
                raise e
    return None


def _search_duckduckgo(query, max_results=30):
    global _ddg_broken
    if _ddg_broken:
        return []
    results = []
    try:
        resp = _retry_request(
            "POST",
            "https://html.duckduckgo.com/html/",
            data={"q": query, "b": ""},
        )
        if not resp or resp.status_code != 200:
            return results

        soup = BeautifulSoup(resp.text, "lxml")

        for r in soup.select(".result"):
            title_a = r.select_one(".result__title a")
            snippet_el = r.select_one(".result__snippet")
            if not title_a:
                continue

            href = title_a.get("href", "")
            if "uddg=" in href:
                m = re.search(r"uddg=([^&]+)", href)
                if m:
                    href = unquote(m.group(1))

            if not href.startswith("http"):
                continue

            results.append({
                "link": href,
                "title": title_a.get_text(strip=True),
                "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
            })

            if len(results) >= max_results:
                break

    except Exception as e:
        print(f"  [DDG] Error: {e}")
        _ddg_broken = True  # skip DDG for all subsequent queries

    return results


def _search_google(query, max_results=30):
    results = []
    seen = set()

    for start in range(0, min(max_results, 40), 10):
        try:
            url = (
                f"https://www.google.com/search"
                f"?q={quote_plus(query)}&num=10&start={start}&hl=en&gl=us"
            )
            resp = _retry_request(
                "GET", url, max_retries=2,
            )

            if not resp or resp.status_code in (429, 503):
                break
            if resp.status_code != 200:
                break

            soup = BeautifulSoup(resp.text, "lxml")

            for g in soup.find_all("div", class_="g"):
                a_tag = g.find("a", href=True)
                h3 = g.find("h3")
                if not a_tag or not h3:
                    continue

                link = a_tag["href"]
                if link.startswith("/url?"):
                    qs = parse_qs(urlparse(link).query)
                    link = qs.get("q", [link])[0]

                if not link.startswith("http") or link in seen:
                    continue
                seen.add(link)

                title = h3.get_text(strip=True)
                snippet = ""
                full = g.get_text(" ", strip=True)
                if title and title in full:
                    snippet = full.split(title, 1)[-1].strip()[:500]

                results.append({"link": link, "title": title, "snippet": snippet})

                if len(results) >= max_results:
                    break

            if len(results) >= max_results:
                break

            time.sleep(random.uniform(3, 6))

        except Exception as e:
            print(f"  [Google] Error: {e}")
            break

    return results


def _search_bing(query, max_results=30):
    results = []
    seen = set()
    try:
        url = f"https://www.bing.com/search?q={quote_plus(query)}&count={min(max_results, 50)}"
        resp = _retry_request("GET", url, max_retries=2)
        if not resp or resp.status_code != 200:
            return results

        soup = BeautifulSoup(resp.text, "lxml")
        for li in soup.select("li.b_algo"):
            a_tag = li.find("a", href=True)
            if not a_tag:
                continue
            link = a_tag["href"]
            if not link.startswith("http") or link in seen:
                continue
            seen.add(link)
            title = a_tag.get_text(strip=True)
            snippet_el = li.select_one(".b_caption p")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            results.append({"link": link, "title": title, "snippet": snippet})
            if len(results) >= max_results:
                break
    except Exception as e:
        print(f"  [Bing] Error: {e}")
    return results


def search(query, max_results=20):
    print(f"    '{query[:70]}' ...", end=" ", flush=True)

    results = _search_duckduckgo(query, max_results)

    if len(results) < 3:
        bing = _search_bing(query, max_results)
        seen = {r["link"] for r in results}
        for r in bing:
            if r["link"] not in seen:
                results.append(r)
                seen.add(r["link"])

    if len(results) < 3:
        fallback = _search_google(query, max_results)
        seen = {r["link"] for r in results}
        for r in fallback:
            if r["link"] not in seen:
                results.append(r)
                seen.add(r["link"])

    print(f"got {len(results)}")
    time.sleep(random.uniform(1, 3))
    return results[:max_results]
