import os
import json
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LinkedInBot:
    def __init__(self, email=None, password=None, headless=False):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        if headless:
            options.add_argument("--headless=new")  # modern headless flag
            
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
        self.email = email
        self.password = password

    def login(self):
        """Login to LinkedIn manually or with provided credentials"""
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(3)

        if self.email and self.password:
            try:
                email_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
                password_field = self.driver.find_element(By.ID, "password")
                submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                
                email_field.send_keys(self.email)
                password_field.send_keys(self.password)
                submit_button.click()
                
                print("✅ Logged in with credentials")
                time.sleep(5)
                
                try:
                    self.wait.until(EC.any_of(
                        EC.presence_of_element_located((By.CLASS_NAME, "global-nav")),
                        EC.presence_of_element_located((By.CLASS_NAME, "feed-container"))
                    ))
                    print("✅ Login successful - Dashboard loaded")
                except:
                    print("⚠️ Login might have failed or requires additional verification")
                    
            except Exception as e:
                print(f"⚠️ Auto login failed: {e}. Please login manually in browser...")
                time.sleep(15)
        else:
            print("⚠️ No credentials provided. Please login manually in the opened browser...")
            input("Press Enter after you've logged in manually...")

    def close(self):
        """Close browser"""
        self.driver.quit()

    def _scroll_and_load(self, n_posts):
        """Scroll until at least n_posts loaded"""
        posts_loaded = 0
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        max_scrolls = 20
        scroll_count = 0

        while posts_loaded < n_posts and scroll_count < max_scrolls:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            post_selectors = [
                "//div[@data-urn and contains(@class, 'update')]",
                "//div[contains(@class, 'feed-shared-update-v2')]",
                "//article[contains(@class, 'artdeco-card')]"
            ]
            
            for selector in post_selectors:
                posts_loaded = len(self.driver.find_elements(By.XPATH, selector))
                if posts_loaded > 0:
                    break

            print(f"📊 Posts loaded: {posts_loaded}/{n_posts}")

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_count += 1
                if scroll_count >= 3:
                    break
            else:
                scroll_count = 0
            last_height = new_height

        print(f"✅ Finished scrolling. Found {posts_loaded} posts")
        return posts_loaded

    def _extract_int(self, text):
        """Convert '1,234' / '1.2K' / '6 comments' like strings to int"""
        if not text:
            return 0
        
        print(f"    _extract_int input: '{text}'")
        
        # First, try to find numbers directly with regex (before cleaning)
        match = re.findall(r"\d+", text)
        print(f"    _extract_int regex matches: {match}")
        
        if match:
            result = int(match[0])
            print(f"    _extract_int final result: {result}")
            return result
        
        # If no numbers found, try the old method
        text_clean = text.lower().replace(",", "").replace(" ", "")
        print(f"    _extract_int cleaned: '{text_clean}'")
        
        if "k" in text_clean:
            try:
                result = int(float(text_clean.replace("k", "")) * 1000)
                print(f"    _extract_int K result: {result}")
                return result
            except:
                return 0
        if "m" in text_clean:
            try:
                result = int(float(text_clean.replace("m", "")) * 1000000)
                print(f"    _extract_int M result: {result}")
                return result
            except:
                return 0

        print(f"    _extract_int no matches found")
        return 0

    def _scrape_posts(self, n_posts, meta):
        """Helper to extract posts (shared between user & hashtag scrapers)"""
        posts = []
        post_selectors = [
            "//div[@data-urn and contains(@class, 'update')]",
            "//div[contains(@class, 'feed-shared-update-v2')]",
            "//article[contains(@class, 'artdeco-card')]"
        ]
        
        post_elements = []
        for selector in post_selectors:
            post_elements = self.driver.find_elements(By.XPATH, selector)
            if post_elements:
                print(f"✅ Found {len(post_elements)} posts using selector: {selector}")
                break
        
        if not post_elements:
            print("❌ No posts found with any selector")
            return posts

        for i, post in enumerate(post_elements[:n_posts]):
            print(f"📝 Scraping post {i+1}/{min(n_posts, len(post_elements))}")
            
            # Extract post text
            text = ""
            text_selectors = [
                ".//div[contains(@class, 'update-components-text')]",
                ".//div[contains(@class, 'feed-shared-text')]",
                ".//div[contains(@class, 'break-words')]",
                ".//span[contains(@dir, 'ltr')]"
            ]
            
            for text_selector in text_selectors:
                try:
                    text_element = post.find_element(By.XPATH, text_selector)
                    text = text_element.text.strip()
                    if text:
                        break
                except:
                    continue

            likes, comments, reposts = 0, 0, 0
            
            # Extract likes/reactions - Updated selectors based on HTML structure
            like_selectors = [
                ".//span[contains(@class, 'social-details-social-counts__reactions-count')]",
                ".//button[contains(@aria-label, 'reactions')]//span[contains(@class, 'social-details-social-counts__reactions-count')]",
                ".//button[@data-reaction-details]//span[contains(@class, 'social-details-social-counts__reactions-count')]"
            ]
            for like_selector in like_selectors:
                try:
                    likes_element = post.find_element(By.XPATH, like_selector)
                    likes_text = likes_element.text.strip()
                    if likes_text:
                        likes = self._extract_int(likes_text)
                        print(f"  Likes found: {likes_text} -> {likes}")
                        break
                except:
                    continue

            # Extract comments - Target the exact HTML structure  
            try:
                comments_span = post.find_element(By.XPATH, ".//li[contains(@class, 'social-details-social-counts__comments')]//span[@aria-hidden='true']")
                comments_text = comments_span.text.strip()
                print(f"  Comments span text found: '{comments_text}'")
                
                if comments_text and 'comment' in comments_text.lower():
                    comments = self._extract_int(comments_text)
                    print(f"  Comments final result: {comments}")
                    
            except Exception as e:
                print(f"  Comments extraction failed: {str(e)}")
                # Fallback to button aria-label
                try:
                    comments_button = post.find_element(By.XPATH, ".//li[contains(@class, 'social-details-social-counts__comments')]//button")
                    aria_label = comments_button.get_attribute('aria-label')
                    if aria_label and 'comment' in aria_label.lower():
                        comments = self._extract_int(aria_label)
                        print(f"  Comments from aria-label: {comments}")
                except:
                    pass

            # Extract reposts/shares - Target the exact HTML structure
            try:
                reposts_button = post.find_element(By.XPATH, ".//button[contains(@aria-label, 'reposts of')]")
                reposts_span = reposts_button.find_element(By.XPATH, ".//span[@aria-hidden='true']")
                reposts_text = reposts_span.text.strip()
                print(f"  Reposts span text found: '{reposts_text}'")
                
                if reposts_text and 'repost' in reposts_text.lower():
                    reposts = self._extract_int(reposts_text)
                    print(f"  Reposts final result: {reposts}")
                    
            except Exception as e:
                print(f"  Reposts extraction failed: {str(e)}")
                # Fallback to button aria-label
                try:
                    reposts_button = post.find_element(By.XPATH, ".//button[contains(@aria-label, 'reposts of')]")
                    aria_label = reposts_button.get_attribute('aria-label')
                    if aria_label and 'repost' in aria_label.lower():
                        reposts = self._extract_int(aria_label)
                        print(f"  Reposts from aria-label: {reposts}")
                except:
                    print("  Reposts: Not found or 0")
                    pass

            post_data = {
                "text": text,
                "likes": likes,
                "comments": comments,
                "reposts": reposts,
                "engagement": likes + comments + reposts,
                "scraped_at": datetime.now().isoformat()
            }
            post_data.update(meta)
            posts.append(post_data)
            
            print(f"  📊 Post {i+1}: Likes={likes}, Comments={comments}, Reposts={reposts}")

        print(f"✅ Successfully scraped {len(posts)} posts")
        return posts

    def scrape_user_posts(self, profile_url, n_posts=5):
        """
        Scrape a given number of posts from a LinkedIn user's profile
        (including text, likes, comments, reposts, engagement).
        """
        print(f"🔍 Visiting profile: {profile_url}")
        self.driver.get(profile_url)
        time.sleep(4)

        # Try to click into posts tab
        try:
            possible_selectors = [
                "a[href*='/recent-activity/posts/']",
                "a[href*='/recent-activity/all/']",
                "a[href*='/recent-activity/']",
                "a[aria-label*='Show all posts']",
            ]
            opened = False
            for selector in possible_selectors:
                try:
                    btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    self.driver.execute_script("arguments[0].click();", btn)
                    print(f"✅ Clicked posts tab using selector: {selector}")
                    time.sleep(4)
                    opened = True
                    break
                except Exception:
                    continue
            if not opened:
                print("⚠️ Could not find 'Show all posts'. Continuing from main profile...")
        except Exception as e:
            print(f"⚠️ Error locating posts tab: {e}")

        print("📜 Scrolling to load posts...")
        self._scroll_and_load(n_posts)

        # Now reuse the same extraction logic as hashtags
        posts = self._scrape_posts(n_posts, {"source": "profile", "profile_url": profile_url})

        print(f"✅ Scraped {len(posts)} posts successfully from profile")
        return posts

    def scrape_hashtag_posts(self, hashtag, n_posts=10):
        """Scrape posts from a LinkedIn hashtag"""
        clean_hashtag = hashtag.lstrip('#').lower()
        url = f"https://www.linkedin.com/feed/hashtag/{clean_hashtag}/"
        
        print(f"🔍 Navigating to hashtag: #{clean_hashtag}")
        self.driver.get(url)
        time.sleep(5)
        
        current_url = self.driver.current_url
        if "hashtag" not in current_url:
            print("❌ Failed to load hashtag page. Trying alternative approach...")
            search_url = f"https://www.linkedin.com/search/results/content/?keywords=%23{clean_hashtag}"
            self.driver.get(search_url)
            time.sleep(5)
        
        print("📜 Scrolling to load hashtag posts...")
        posts_found = self._scroll_and_load(n_posts)
        
        if posts_found == 0:
            print("⚠️ No hashtag posts found.")
            return []

        return self._scrape_posts(n_posts, {"source": "hashtag", "hashtag": clean_hashtag})

    def export_to_json(self, data, custom_folder="data", prefix="linkedin_posts"):
        """Save scraped data to JSON file"""
        if not data:
            print("⚠️ No data to export")
            return None
            
        os.makedirs(custom_folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.json"
        filepath = os.path.join(custom_folder, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Data exported to: {filepath}")
            print(f"📊 Total posts exported: {len(data)}")
            return filepath
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return None