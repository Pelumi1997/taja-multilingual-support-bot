from pathlib import Path

from taja_bot.services.faq import FaqService


if __name__ == "__main__":
    data_path = Path(__file__).resolve().parents[1] / "src" / "taja_bot" / "data" / "faqs.json"
    service = FaqService(data_path)
    print(f"Validated {len(service)} multilingual FAQ entries from {data_path}")
