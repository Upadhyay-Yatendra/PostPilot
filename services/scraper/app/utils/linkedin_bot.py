import os
import asyncio
import shutil
import re
from datetime import datetime, timezone, timedelta
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


class LinkedInBot:
    def __init__(self, email=None, password=None, headless=True, debug=False, slow_mo=None):
        self.email = email
        self.password = password
        self.headless = headless
        self.debug = debug
        self.slow_mo = slow_mo
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self, state_file=None):
        """Start Playwright and browser with persistent session"""
        self.playwright = await async_playwright().start()
        
        # Set default state file path relative to the bot's location
        if state_file is None:
            # Get the directory where this file is located
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up two levels: from app/utils/ to services/scraper/
            scraper_dir = os.path.dirname(os.path.dirname(current_dir))
            self.state_file = os.path.join(scraper_dir, "state.json")
        else:
            self.state_file = state_file

        launch_options = {
            "headless": self.headless,
            "args": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
            ],
            "timeout": 60000
        }
        
        if self.slow_mo:
            launch_options["slow_mo"] = self.slow_mo
        if not self.headless and self.debug:
            launch_options["devtools"] = True

        try:
            self.browser = await self.playwright.chromium.launch(**launch_options)
        except Exception as e:
            print(f"⚠️ Chromium launch failed: {e}")
            chrome_path = self._find_chrome_executable()
            if chrome_path:
                launch_options["executable_path"] = chrome_path
                self.browser = await self.playwright.chromium.launch(**launch_options)
            else:
                raise

        # Check if state file exists and load it
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/120.0.0.0 Safari/537.36",
            "locale": "en-US"
        }
        
        # Load existing session state if available
        if os.path.exists(self.state_file):
            try:
                context_options["storage_state"] = self.state_file
                print(f"📂 Loading existing session from {self.state_file}")
            except Exception as e:
                print(f"⚠️ Failed to load session state: {e}")
                print("🔥 Starting fresh session...")
        else:
            print(f"🔍 No existing session found at {self.state_file}, starting fresh...")

        self.context = await self.browser.new_context(**context_options)
        
        # Block unnecessary resources to speed up loading
        await self.context.route("**/*.{woff,woff2}", lambda route: route.abort())
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(60000)

        if self.debug:
            self.page.on("console", lambda msg: print(f"🖥 Console: {msg.text}"))
            self.page.on("response", lambda response: print(f"📡 Response: {response.status} {response.url}"))

        print("✅ Browser started")

    async def login(self, manual_wait=False, force_login=False):
        """Login into LinkedIn with session persistence"""
        try:
            # First, check if we're already logged in by checking for LinkedIn main page elements
            if not force_login:
                print("🔍 Checking if already logged in...")
                await self.page.goto("https://www.linkedin.com/feed", wait_until="domcontentloaded")
                await asyncio.sleep(3)
                
                # Check if we can find the search box (indicates we're logged in)
                search_box = await self.page.query_selector("input[placeholder*='Search']")
                if search_box:
                    print("✅ Already logged in using saved session!")
                    return True
                else:
                    print("🔥 Session expired or invalid, proceeding with fresh login...")
            
            print("🔍 Navigating to LinkedIn login...")
            await self.page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
            
            # Wait for login form
            await self.page.wait_for_selector("input#username", timeout=10000)
            
            # Fill credentials
            await self.page.fill("input#username", self.email)
            await asyncio.sleep(1)
            await self.page.fill("input#password", self.password)
            await asyncio.sleep(1)
            
            # Click login button
            await self.page.click("button[type='submit']")
            print("🔍 Login submitted...")
            
            # Wait for successful login or CAPTCHA/2FA
            try:
                # Try to wait for the main LinkedIn page
                await self.page.wait_for_selector("input[placeholder*='Search']", timeout=15000)
                print("✅ Login successful")
                
                # Save session state after successful login
                await self._save_session_state()
                return True
                
            except PlaywrightTimeoutError:
                # Check for CAPTCHA or verification
                captcha_present = await self.page.query_selector("iframe[title*='reCAPTCHA']")
                verification_present = await self.page.query_selector("input[name='pin']")
                
                if captcha_present or verification_present or manual_wait:
                    print("⚠️ CAPTCHA/2FA detected or manual wait requested...")
                    print("🚨 MANUAL ACTION REQUIRED:")
                    print("   1. Complete 2FA/CAPTCHA verification in the browser")
                    print("   2. Wait for redirect to LinkedIn feed")
                    print("   3. Session will be automatically saved")
                    
                    if manual_wait:
                        await asyncio.sleep(30)
                    else:
                        # Wait for user to complete verification (extended timeout)
                        print("⏳ Waiting up to 5 minutes for manual verification...")
                        for i in range(300):  # Wait up to 5 minutes
                            try:
                                await self.page.wait_for_selector("input[placeholder*='Search']", timeout=1000)
                                print("✅ Login successful after verification")
                                
                                # Save session state after successful manual login
                                await self._save_session_state()
                                return True
                            except PlaywrightTimeoutError:
                                if i % 30 == 0:  # Print progress every 30 seconds
                                    remaining = (300 - i) // 60
                                    print(f"⏳ Still waiting... ({remaining} minutes remaining)")
                                continue
                    
                    # Final check
                    search_box = await self.page.query_selector("input[placeholder*='Search']")
                    if search_box:
                        print("✅ Login successful")
                        await self._save_session_state()
                        return True
                    else:
                        print("❌ Login verification timeout. Please run in non-headless mode for manual completion.")
                        print("💡 Tip: Run with headless=False to complete 2FA manually, then switch back to headless=True")
                        raise Exception("Login failed - verification timeout")
                else:
                    raise Exception("Login failed - unknown error")
                    
        except Exception as e:
            print(f"❌ Login error: {e}")
            raise

    async def _save_session_state(self):
        """Save current session state to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            # Save the storage state (cookies, localStorage, etc.)
            await self.context.storage_state(path=self.state_file)
            print(f"💾 Session state saved to {self.state_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to save session state: {e}")

    async def ensure_logged_in(self):
        """Utility method to ensure user is logged in before scraping"""
        try:
            # Quick check if we're on a LinkedIn page and logged in
            current_url = self.page.url
            if "linkedin.com" not in current_url:
                await self.page.goto("https://www.linkedin.com/feed", wait_until="domcontentloaded")
            
            # Check for search box
            search_box = await self.page.query_selector("input[placeholder*='Search']")
            if not search_box:
                print("🔥 Session expired, attempting re-login...")
                return await self.login(force_login=True)
            
            return True
        except Exception as e:
            print(f"⚠️ Login check failed: {e}")
            return False

    async def scrape_user_posts(self, profile_url, n_posts=5):
        """Scrape posts from LinkedIn profile with enhanced selectors and data extraction"""
        try:
            # Ensure we're logged in before scraping
            if not await self.ensure_logged_in():
                raise Exception("Failed to ensure login status")
            
            print(f"🔍 Navigating to profile: {profile_url}")
            await self.page.goto(profile_url, wait_until="domcontentloaded")
            
            # Wait for page to load
            await asyncio.sleep(4)
            
            # Try to click into posts tab
            print("🔍 Looking for 'Show all posts' button...")
            posts_tab_clicked = False
            
            post_tab_selectors = [
                "footer a.profile-creator-shared-content-view__footer-action:has-text('Show all posts')",
                "a.profile-creator-shared-content-view__footer-action:has-text('Show all posts')",
                "a.profile-creator-shared-content-view__footer-action.artdeco-button",
                "a[href*='/recent-activity/all/']",
                "a[href*='/recent-activity/posts/']",
                "a[href*='/recent-activity/']",
                "a:has-text('Show all posts')",
                "button:has-text('Show all posts')"
            ]
            
            for selector in post_tab_selectors:
                try:
                    print(f"🔍 Trying selector: {selector}")
                    posts_tab = await self.page.wait_for_selector(selector, timeout=8000)
                    if posts_tab:
                        button_text = await posts_tab.inner_text()
                        print(f"✅ Found element with text: '{button_text.strip()}'")
                        
                        if "show all posts" in button_text.lower():
                            print(f"✅ Found correct 'Show all posts' button with selector: {selector}")
                            
                            await posts_tab.scroll_into_view_if_needed()
                            await asyncio.sleep(1)
                            await posts_tab.click()
                            await asyncio.sleep(4)
                            
                            current_url = self.page.url
                            if "recent-activity" in current_url:
                                posts_tab_clicked = True
                                print("✅ Successfully navigated to posts page")
                                break
                            else:
                                print("⚠️ Click registered but URL didn't change to posts page")
                        else:
                            print(f"⚠️ Element found but text doesn't match: '{button_text}'")
                            
                except PlaywrightTimeoutError:
                    print(f"⏰ Timeout waiting for selector: {selector}")
                    continue
                except Exception as e:
                    if self.debug:
                        print(f"⚠️ Error with selector {selector}: {e}")
                    continue
            
            if not posts_tab_clicked:
                print("⚠️ Could not find 'Show all posts'. Continuing from main profile...")
            
            # Scroll and load posts
            print("📜 Scrolling to load posts...")
            await self._scroll_and_load(n_posts)
            
            posts_data = []
            
            post_selectors = [
                "div[data-urn*='activity']",
                "div.feed-shared-update-v2",
                "article.artdeco-card"
            ]
            
            posts = []
            for selector in post_selectors:
                try:
                    posts = await self.page.query_selector_all(selector)
                    if posts:
                        print(f"✅ Found {len(posts)} posts with selector: {selector}")
                        break
                except:
                    continue
            
            if not posts:
                print("❌ No posts found with any selector")
                return []
            
            # Process posts using improved extraction
            for i, post in enumerate(posts[:n_posts]):
                if len(posts_data) >= n_posts:
                    break
                
                print(f"🔍 Scraping post {i+1}/{min(n_posts, len(posts))}")
                
                try:
                    # Extract post content
                    post_text = await self._extract_post_content(post)
                    if not post_text or len(post_text.strip()) < 10:
                        continue
                    
                    # Extract engagement metrics
                    metrics = await self._extract_engagement_metrics_improved(post)
                    
                    # Create unique identifier for deduplication
                    post_id = f"{post_text[:50]}_{metrics.get('likes', 0)}"
                    
                    # Check for duplicates
                    if any(existing_post.get('id') == post_id for existing_post in posts_data):
                        continue
                    
                    post_data = {
                        "id": post_id,
                        "text": post_text,
                        "likes": metrics.get("likes", 0),
                        "comments": metrics.get("comments", 0),
                        "reposts": metrics.get("reposts", 0),
                        "engagement": metrics.get("engagement", 0),
                        "scraped_at": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
                        "source": "profile",
                        "profile_url": profile_url
                    }
                    
                    posts_data.append(post_data)
                    
                    print(f"  📊 Post {i+1}: Likes={metrics['likes']}, Comments={metrics['comments']}, Reposts={metrics['reposts']}")
                    
                    if self.debug:
                        print(f"🔍 Post text: {post_text[:100]}...")
                        
                except Exception as e:
                    if self.debug:
                        print(f"⚠️ Error processing post {i}: {e}")
                    continue
            
            print(f"✅ Scraped {len(posts_data)} posts from {profile_url}")
            return posts_data
            
        except Exception as e:
            print(f"❌ Error scraping profile posts: {e}")
            return []

    async def scrape_hashtag_posts(self, hashtag, n_posts=5):
        """Scrape posts for a specific hashtag"""
        try:
            # Ensure we're logged in before scraping
            if not await self.ensure_logged_in():
                raise Exception("Failed to ensure login status")
                
            # Clean hashtag
            clean_hashtag = hashtag.lstrip('#')
            hashtag_url = f"https://www.linkedin.com/feed/hashtag/{clean_hashtag}/"
            
            print(f"🏷️ Navigating to hashtag: #{clean_hashtag}")
            await self.page.goto(hashtag_url, wait_until="domcontentloaded")
            await asyncio.sleep(5)
            
            # Check if we're on the right page
            current_url = self.page.url
            if "hashtag" not in current_url:
                print("❌ Failed to load hashtag page. Trying alternative approach...")
                search_url = f"https://www.linkedin.com/search/results/content/?keywords=%23{clean_hashtag}"
                await self.page.goto(search_url, wait_until="domcontentloaded")
                await asyncio.sleep(5)
            
            print("📜 Scrolling to load hashtag posts...")
            posts_found = await self._scroll_and_load(n_posts)
            
            if posts_found == 0:
                print("⚠️ No hashtag posts found.")
                return []

            return await self._scrape_posts_generic(n_posts, {"source": "hashtag", "hashtag": clean_hashtag})
                    
        except Exception as e:
            print(f"❌ Error scraping hashtag posts: {e}")
            return []

    async def _scroll_and_load(self, n_posts):
        """Scroll until at least n_posts loaded"""
        posts_loaded = 0
        last_height = await self.page.evaluate("document.body.scrollHeight")
        max_scrolls = 20
        scroll_count = 0
        
        while posts_loaded < n_posts and scroll_count < max_scrolls:
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(3)
            
            post_selectors = [
                "div[data-urn*='activity']",
                "div.feed-shared-update-v2", 
                "article.artdeco-card"
            ]
            
            for selector in post_selectors:
                try:
                    posts = await self.page.query_selector_all(selector)
                    posts_loaded = len(posts)
                    if posts_loaded > 0:
                        break
                except:
                    continue
            
            print(f"📊 Posts loaded: {posts_loaded}/{n_posts}")
            
            new_height = await self.page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                scroll_count += 1
                if scroll_count >= 3:
                    break
            else:
                scroll_count = 0
            last_height = new_height
        
        print(f"✅ Finished scrolling. Found {posts_loaded} posts")
        return posts_loaded

    async def _extract_engagement_metrics_improved(self, post_element):
        """Extract likes, comments, reposts using the same logic as Selenium version"""
        metrics = {"likes": 0, "comments": 0, "reposts": 0, "engagement": 0}
        
        try:
            # Extract likes/reactions
            like_selectors = [
                "span.social-details-social-counts__reactions-count",
                "button[data-reaction-details] span.social-details-social-counts__reactions-count",
                "button[aria-label*='reactions'] span.social-details-social-counts__reactions-count"
            ]
            
            for like_selector in like_selectors:
                try:
                    likes_element = await post_element.query_selector(like_selector)
                    if likes_element:
                        likes_text = await likes_element.inner_text()
                        if likes_text:
                            metrics["likes"] = self._extract_int(likes_text.strip())
                            if self.debug:
                                print(f"  Likes found: {likes_text} -> {metrics['likes']}")
                            break
                except:
                    continue
            
            # Extract comments
            try:
                comments_span = await post_element.query_selector("li.social-details-social-counts__comments span[aria-hidden='true']")
                if comments_span:
                    comments_text = await comments_span.inner_text()
                    if self.debug:
                        print(f"  Comments span text found: '{comments_text}'")
                    
                    if comments_text and 'comment' in comments_text.lower():
                        metrics["comments"] = self._extract_int(comments_text.strip())
                        if self.debug:
                            print(f"  Comments final result: {metrics['comments']}")
                else:
                    raise Exception("Comments span not found")
                    
            except Exception as e:
                if self.debug:
                    print(f"  Comments extraction failed: {str(e)}")
                # Fallback to button aria-label
                try:
                    comments_button = await post_element.query_selector("li.social-details-social-counts__comments button")
                    if comments_button:
                        aria_label = await comments_button.get_attribute('aria-label')
                        if aria_label and 'comment' in aria_label.lower():
                            metrics["comments"] = self._extract_int(aria_label)
                            if self.debug:
                                print(f"  Comments from aria-label: {metrics['comments']}")
                except:
                    pass
            
            # Extract reposts/shares
            try:
                reposts_button = await post_element.query_selector("button[aria-label*='reposts of']")
                if reposts_button:
                    reposts_span = await reposts_button.query_selector("span[aria-hidden='true']")
                    if reposts_span:
                        reposts_text = await reposts_span.inner_text()
                        if self.debug:
                            print(f"  Reposts span text found: '{reposts_text}'")
                        
                        if reposts_text and 'repost' in reposts_text.lower():
                            metrics["reposts"] = self._extract_int(reposts_text.strip())
                            if self.debug:
                                print(f"  Reposts final result: {metrics['reposts']}")
                else:
                    raise Exception("Reposts button not found")
                    
            except Exception as e:
                if self.debug:
                    print(f"  Reposts extraction failed: {str(e)}")
                # Fallback to button aria-label
                try:
                    reposts_button = await post_element.query_selector("button[aria-label*='reposts of']")
                    if reposts_button:
                        aria_label = await reposts_button.get_attribute('aria-label')
                        if aria_label and 'repost' in aria_label.lower():
                            metrics["reposts"] = self._extract_int(aria_label)
                            if self.debug:
                                print(f"  Reposts from aria-label: {metrics['reposts']}")
                except:
                    if self.debug:
                        print("  Reposts: Not found or 0")
                    pass
            
            # Calculate total engagement
            metrics["engagement"] = metrics["likes"] + metrics["comments"] + metrics["reposts"]
            
        except Exception as e:
            if self.debug:
                print(f"⚠️ Error extracting engagement metrics: {e}")
        
        return metrics

    async def _scrape_posts_generic(self, n_posts, meta):
        """Generic post scraper used by both user and hashtag methods"""
        posts = []
        post_selectors = [
            "div[data-urn*='activity']",
            "div.feed-shared-update-v2",
            "article.artdeco-card"
        ]
        
        post_elements = []
        for selector in post_selectors:
            try:
                post_elements = await self.page.query_selector_all(selector)
                if post_elements:
                    print(f"✅ Found {len(post_elements)} posts using selector: {selector}")
                    break
            except:
                continue
        
        if not post_elements:
            print("❌ No posts found with any selector")
            return posts

        for i, post in enumerate(post_elements[:n_posts]):
            print(f"🔍 Scraping post {i+1}/{min(n_posts, len(post_elements))}")
            
            try:
                # Extract post text
                text = await self._extract_post_content(post)
                if not text or len(text.strip()) < 10:
                    continue

                # Extract engagement metrics
                metrics = await self._extract_engagement_metrics_improved(post)

                post_data = {
                    "text": text,
                    "likes": metrics["likes"],
                    "comments": metrics["comments"], 
                    "reposts": metrics["reposts"],
                    "engagement": metrics["engagement"],
                    "scraped_at": datetime.now().isoformat()
                }
                post_data.update(meta)
                posts.append(post_data)
                
                print(f"  📊 Post {i+1}: Likes={metrics['likes']}, Comments={metrics['comments']}, Reposts={metrics['reposts']}")

            except Exception as e:
                if self.debug:
                    print(f"⚠️ Error processing post {i}: {e}")
                continue

        print(f"✅ Successfully scraped {len(posts)} posts")
        return posts

    async def _extract_post_content(self, post_element):
        """Extract post text content with multiple fallback strategies"""
        try:
            content_selectors = [
                "div.update-components-text",
                "div.feed-shared-text",
                "div.break-words",
                "span[dir='ltr']"
            ]
            
            for selector in content_selectors:
                try:
                    content_element = await post_element.query_selector(selector)
                    if content_element:
                        text = await content_element.inner_text()
                        if text and len(text.strip()) > 10:
                            # Clean the text
                            text = re.sub(r'\s+', ' ', text.strip())
                            text = re.sub(r'…see more$', '', text)
                            return text
                except:
                    continue
            
            # Fallback: get all text from post
            all_text = await post_element.inner_text()
            if all_text:
                # Remove common LinkedIn UI text
                cleaned_text = re.sub(r'(Like|Comment|Repost|Send|Share|\d+\s*(likes?|comments?|reposts?))', '', all_text)
                cleaned_text = re.sub(r'\s+', ' ', cleaned_text.strip())
                if len(cleaned_text) > 10:
                    return cleaned_text[:500]  # Limit length
            
            return ""
            
        except Exception as e:
            if self.debug:
                print(f"⚠️ Error extracting post content: {e}")
            return ""

    def _extract_int(self, text):
        """Convert '1,234' / '1.2K' / '6 comments' like strings to int"""
        if not text:
            return 0
        
        if self.debug:
            print(f"    _extract_int input: '{text}'")
        
        # First, try to find numbers directly with regex
        match = re.findall(r"\d+", text)
        if self.debug:
            print(f"    _extract_int regex matches: {match}")
        
        if match:
            result = int(match[0])
            if self.debug:
                print(f"    _extract_int final result: {result}")
            return result
        
        # If no numbers found, try the K/M conversion
        text_clean = text.lower().replace(",", "").replace(" ", "")
        if self.debug:
            print(f"    _extract_int cleaned: '{text_clean}'")
        
        if "k" in text_clean:
            try:
                result = int(float(text_clean.replace("k", "")) * 1000)
                if self.debug:
                    print(f"    _extract_int K result: {result}")
                return result
            except:
                return 0
        if "m" in text_clean:
            try:
                result = int(float(text_clean.replace("m", "")) * 1000000)
                if self.debug:
                    print(f"    _extract_int M result: {result}")
                return result
            except:
                return 0

        if self.debug:
            print(f"    _extract_int no matches found")
        return 0

    def _find_chrome_executable(self):
        """Find Chrome path if Chromium fails"""
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return shutil.which("chrome") or shutil.which("google-chrome") or shutil.which("chromium")

    async def close(self, keep_open=False):
        """Close browser unless debugging"""
        if keep_open:
            print("🔍 Debug mode: keeping browser open")
            return
        
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            print("✅ Browser closed")
        except Exception as e:
            print(f"⚠️ Error closing browser: {e}")