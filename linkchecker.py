import streamlit as st
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse, urljoin, urldefrag

async def check_link(session, base_url, href, cache, timeout=30):
    try:
        absolute_url = urljoin(base_url, href)
        if absolute_url in cache:
            return None  # Skip if already checked

        async with session.get(absolute_url, timeout=timeout) as response:
            response.raise_for_status()
            # Read the response to ensure it is fully processed
            await response.read()

    except asyncio.TimeoutError:
        st.warning(f"Timeout occurred while checking {absolute_url}")
        return absolute_url
    except aiohttp.ClientError:
        return absolute_url
    finally:
        cache.add(absolute_url)  # Cache the result

    return None



async def check_broken_links_with_ui(url, max_connections=10, timeout=30):
    start_time = time.time()
    broken_links = set()
    cache = set()

    try:
        async with aiohttp.ClientSession() as session:
            response = await session.get(url, timeout=timeout)
            response.raise_for_status()

            base_url = urlparse(url).scheme + "://" + urlparse(url).hostname

            soup = BeautifulSoup(await response.text(), "html.parser")
            links_to_check = [link.get("href") for link in soup.find_all("a") if link.get("href") and not link.get("href").startswith("#") and not link.get("href").startswith("javascript:")and not link.get("href").startswith("http")]

            tasks = [check_link(session, base_url, href, cache, timeout) for href in links_to_check]

            results = await asyncio.gather(*tasks)

        elapsed_time = time.time() - start_time
        if elapsed_time > 30:
            st.warning("Function exceeded 30-second limit. Review for further optimization.")

        return list(filter(None, results))

    except aiohttp.ClientError as e:
        st.error(f"Error fetching URL: {e}")
        return []

# Streamlit app setup
st.title("Broken Link Checker")

url = st.text_input("Enter the website URL to check:")

if url:
    with st.spinner("Checking for broken links..."):
        broken_links = asyncio.run(check_broken_links_with_ui(url))

    if broken_links:
        st.header("Broken Links Found:")
        st.write(broken_links)
    else:
        st.success("No broken links found!")
