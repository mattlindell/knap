import logging
import os
import re
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler

from jinja2 import Environment, FileSystemLoader
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config import load_config, DEFAULT_CONFIG
from extractors.classifier import classify_url, ContentType
from extractors.video import extract_video_content
from extractors.article import extract_article_content
from extractors.quality_gate import check_content_quality
from llm.factory import create_provider

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, "templates")
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")

logger = logging.getLogger("knap")


def setup_logging(level: int = logging.INFO) -> str:
    """Configure rotating file logging (and console output when available).

    Writes to ``logs/clipping_watcher.log`` next to this script, rotating at
    1 MB with three backups. A console handler is added only when a real stdout
    exists -- under ``pythonw.exe`` (the hidden launch path) ``sys.stdout`` is
    ``None``, so the file handler is the sole sink. Returns the log file path.
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, "clipping_watcher.log")

    logger.setLevel(level)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-7s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = RotatingFileHandler(
        log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    if sys.stdout is not None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(fmt)
        logger.addHandler(console_handler)

    return log_path


class ClippingProcessor(FileSystemEventHandler):
    def __init__(self, config: dict):
        self.clippings_dir = config["paths"]["clippings_dir"]
        self.processed_dir = config["paths"]["processed_dir"]
        self.min_content_length = config.get("extraction", {}).get(
            "min_content_length", 100
        )

        # Merge user summarization settings over the built-in defaults so any
        # omitted key still has a sane value.
        self.summarization = {
            **DEFAULT_CONFIG["summarization"],
            **config.get("summarization", {}),
        }

        self.jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR), keep_trailing_newline=True
        )

        self.llm_provider = create_provider(config["llm"])

        os.makedirs(self.processed_dir, exist_ok=True)

        logger.info("Watching: %s", self.clippings_dir)
        logger.info("Processing to: %s", self.processed_dir)

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = str(event.src_path)

        if not file_path.lower().endswith(".md"):
            return

        logger.info("New clipping detected: %s", os.path.basename(file_path))

        # Wait a moment for the file to be fully written
        time.sleep(2)

        self.process_clipping(file_path)

    def extract_metadata_from_clipping(self, file_path: str) -> dict | None:
        """Extract URL, author, title, published date, and original content."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            metadata = {
                "url": "",
                "author": "",
                "published": "",
                "title": "",
                "original_content": content,
            }

            # Look for URL in various formats
            url_patterns = [
                r'source:\s*"?([^"\n]+)"?',  # YAML frontmatter
                r'url:\s*"?([^"\n]+)"?',  # Alternative YAML
                r"https?://[^\s\)]+",  # Any HTTP URL
            ]

            for pattern in url_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    url = matches[0].strip()
                    if url.startswith("http"):
                        metadata["url"] = url
                        break

            # Extract author - handle both single author and list format
            author_match = re.search(
                r'author:\s*\n?\s*-?\s*"?\[\[(.+?)\]\]"?',
                content,
                re.IGNORECASE | re.MULTILINE,
            )
            if not author_match:
                author_match = re.search(
                    r'author:\s*"?([^"\n]+)"?', content, re.IGNORECASE
                )

            if author_match:
                metadata["author"] = author_match.group(1).strip()

            # Extract published date
            published_match = re.search(
                r'published:\s*"?([^"\n]+)"?', content, re.IGNORECASE
            )
            if published_match:
                metadata["published"] = published_match.group(1).strip()

            # Extract title from frontmatter
            title_match = re.search(
                r'title:\s*"?([^"\n]+)"?', content, re.IGNORECASE
            )
            if title_match:
                metadata["title"] = title_match.group(1).strip().strip('"')

            if not metadata["url"]:
                logger.warning("No URL found in clipping")
                return None

            return metadata

        except Exception:
            logger.exception("Error reading clipping file")
            return None

    def _get_original_excerpt(self, content: str, max_length: int = 1000) -> str:
        """Strip YAML frontmatter, return body text truncated to max_length."""
        # Remove YAML frontmatter
        stripped = re.sub(r"^---\s*\n.*?\n---\s*\n?", "", content, count=1, flags=re.DOTALL)
        body = stripped.strip()

        if len(body) > max_length:
            return body[:max_length] + "\n\n[Excerpt truncated]"
        return body

    def process_clipping(self, file_path: str) -> None:
        """Process a single clipping file through the full pipeline."""
        try:
            # 1. Extract metadata
            clipping_metadata = self.extract_metadata_from_clipping(file_path)
            if not clipping_metadata:
                logger.info("Skipping - no URL found")
                return

            url = clipping_metadata["url"]
            title = clipping_metadata.get("title", "Untitled")
            author = clipping_metadata.get("author", "Unknown")
            published = clipping_metadata.get("published", "Unknown")
            original_content = clipping_metadata.get("original_content", "")

            logger.info("Processing URL: %s", url)

            # 2. Classify URL
            content_type = classify_url(url)

            # 3. Route to appropriate extractor
            if content_type == ContentType.VIDEO:
                result = extract_video_content(url)
            else:
                result = extract_article_content(url)

            # 4. Check quality gate
            quality_ok = check_content_quality(result, self.min_content_length)

            # Common template variables
            template_vars = {
                "title": title,
                "source": url,
                "author": author or "Unknown",
                "published": published,
                "created": datetime.now().strftime("%Y-%m-%d"),
            }

            # 5. Build output
            if quality_ok:
                # Build LLM prompt. Feed as much of the extracted text as the
                # configured input budget allows -- the model has a large
                # context window, so we no longer truncate to a few thousand
                # characters.
                content = result.text[: self.summarization["max_input_chars"]]
                prompt = f"""Please analyze this content and provide a structured summary.

Title: {title}
URL: {url}
Content: {content}

Please respond in this exact format:

**SUMMARY:**
[Provide a concise 2-3 sentence summary of the main points]

**KEY CONCEPTS:**
- [Key concept 1]
- [Key concept 2]
- [Key concept 3]

**SUGGESTED CATEGORY:**
[Suggest whether this belongs in: Attention Deficit Disorder, Home Automation, AI and LLMs, Servers and Infrastructure, Development, Management, Operating Systems, Jeep, Dog, Design, or Other]
"""
                logger.info("Sending to LLM for processing...")
                llm_response = self.llm_provider.summarize(
                    prompt,
                    system=self.summarization["system_prompt"],
                    temperature=self.summarization["temperature"],
                    max_tokens=self.summarization["max_tokens"],
                    timeout=self.summarization["request_timeout"],
                    max_retries=self.summarization["max_retries"],
                )

                if llm_response:
                    template = self.jinja_env.get_template("summary.md.j2")
                    template_vars["llm_summary"] = llm_response
                    output = template.render(**template_vars)
                else:
                    # LLM failed -- fall through to failed path
                    logger.warning("LLM failed, using failed extraction template")
                    template = self.jinja_env.get_template("failed_extraction.md.j2")
                    template_vars["original_excerpt"] = self._get_original_excerpt(
                        original_content
                    )
                    output = template.render(**template_vars)
            else:
                # Quality gate failed
                logger.warning(
                    "Content quality below threshold, using failed extraction template"
                )
                template = self.jinja_env.get_template("failed_extraction.md.j2")
                template_vars["original_excerpt"] = self._get_original_excerpt(
                    original_content
                )
                output = template.render(**template_vars)

            # 6. Save processed file
            safe_title = re.sub(r'[<>:"/\\|?*]', "", title)[:50]
            processed_filename = (
                f"{safe_title}_{datetime.now().strftime('%Y%m%d')}.md"
            )
            processed_path = os.path.join(self.processed_dir, processed_filename)

            with open(processed_path, "w", encoding="utf-8") as f:
                f.write(output)

            logger.info("Processed and saved: %s", processed_filename)

        except Exception:
            logger.exception("Error processing clipping: %s", file_path)


def main():
    log_path = setup_logging()
    config = load_config()

    clippings_dir = config["paths"]["clippings_dir"]
    if not os.path.exists(clippings_dir):
        logger.error("Clippings directory not found: %s", clippings_dir)
        logger.error("Please update config.yaml with the correct path")
        return

    processor = ClippingProcessor(config)
    observer = Observer()
    observer.schedule(processor, clippings_dir, recursive=False)

    observer.start()
    logger.info("Folder watcher started -- logging to %s", log_path)
    logger.info("Waiting for new clippings... (Ctrl+C to stop)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Stopping folder watcher...")

    observer.join()


if __name__ == "__main__":
    main()
