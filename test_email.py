#!/usr/bin/env python3
"""
Test script to generate and optionally send the email report locally.

Usage:
  # Just generate the report (no email sent):
  python test_email.py

  # Generate and send a test email:
  python test_email.py --send --to you@example.com \
      --smtp-user user@gmail.com --smtp-pass 'app-password'
"""

import argparse
import json
import smtplib
import sys
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from main import generate_email_report

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


def main():
    parser = argparse.ArgumentParser(description="Test email report generation and sending")
    parser.add_argument("--send", action="store_true", help="Actually send the email")
    parser.add_argument("--to", help="Recipient email address")
    parser.add_argument("--smtp-user", help="SMTP username (Gmail address)")
    parser.add_argument("--smtp-pass", help="SMTP password (Gmail App Password)")
    parser.add_argument("--smtp-host", default="smtp.gmail.com", help="SMTP server")
    parser.add_argument("--smtp-port", type=int, default=465, help="SMTP port")
    parser.add_argument("--num-papers", type=int, default=5,
                        help="Number of papers to include in test report (default: 5)")
    args = parser.parse_args()

    # Load existing papers to use as sample data
    papers_path = Path(__file__).parent / "data" / "papers.json"
    with open(papers_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    papers = data["papers"]
    sample_papers = [p for p in papers if p.get("summary_status") == "success"][:args.num_papers]

    if not sample_papers:
        print("No papers with successful summaries found in data/papers.json")
        sys.exit(1)

    # Generate the report
    output_path = Path(__file__).parent / "data" / "email_report.md"
    usage_stats = {"input_tokens": 12345, "output_tokens": 6789, "total_tokens": 19134}

    generate_email_report(
        new_papers=sample_papers,
        retry_papers=[],
        failed_papers=[],
        total_count=len(papers),
        usage_stats=usage_stats,
        output_path=output_path,
        site_url="https://example.github.io/paper-pulse/",
    )

    print(f"\nGenerated report at: {output_path}")
    print(f"Report size: {output_path.stat().st_size} bytes")
    print(f"Papers included: {len(sample_papers)}")

    # Print preview
    content = output_path.read_text(encoding="utf-8")
    preview_lines = content.split("\n")[:30]
    print("\n--- Preview (first 30 lines) ---")
    print("\n".join(preview_lines))
    print("--- End preview ---\n")

    if not args.send:
        print("To send a test email, run:")
        print("  python test_email.py --send --to you@example.com "
              "--smtp-user user@gmail.com --smtp-pass 'app-password'")
        return

    # Validate send args
    if not args.to or not args.smtp_user or not args.smtp_pass:
        print("Error: --to, --smtp-user, and --smtp-pass are required when using --send")
        sys.exit(1)

    # Convert markdown to HTML if possible, otherwise send as plain text
    if HAS_MARKDOWN:
        html = markdown.markdown(content, extensions=["tables", "fenced_code"])
        msg = MIMEText(html, "html", "utf-8")
    else:
        msg = MIMEText(content, "plain", "utf-8")
        print("Note: 'markdown' package not installed, sending as plain text.")
        print("      Install with: pip install markdown")

    msg["Subject"] = f"[TEST] Paper Pulse Daily Report - {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
    msg["From"] = f"Paper Pulse Bot <{args.smtp_user}>"
    msg["To"] = args.to

    print(f"Sending email to {args.to} via {args.smtp_host}:{args.smtp_port}...")
    with smtplib.SMTP_SSL(args.smtp_host, args.smtp_port) as server:
        server.login(args.smtp_user, args.smtp_pass)
        server.sendmail(args.smtp_user, [args.to], msg.as_string())

    print("Email sent successfully!")


if __name__ == "__main__":
    main()
