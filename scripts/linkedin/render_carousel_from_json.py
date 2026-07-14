#!/usr/bin/env python3
"""
Daanaa Carousel Renderer — JSON to PDF

Reads carousel JSON data files and renders perfect PDFs.
No LLM intermediary. Data in, PDF out. Guaranteed consistency.

Usage:
  python3 render_carousel_from_json.py carousels/sample_1_reserve_crisis.json
  python3 render_carousel_from_json.py carousels/*.json  # batch
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw

# Import existing carousel generators
sys.path.insert(0, str(Path(__file__).parent))
import carousel_generator as gen

def load_carousel_json(filepath):
    """Load and validate carousel JSON."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data

def render_carousel_from_json(json_data, output_dir=None):
    """
    Render a carousel from JSON data.

    Args:
        json_data: Dict with carousel_type, title, slides
        output_dir: Where to save the PDF (default: scripts/linkedin/output)

    Returns:
        Path to generated PDF
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    # Load fonts once
    fonts = gen.load_fonts()

    # Render slides; collect clickable regions (image coords, top-left origin)
    slides = []
    link_annots = []  # (page_index, (x0, y0, x1, y1), url)
    total_slides = len(json_data["slides"])

    for slide_num, slide in enumerate(json_data["slides"], start=1):
        slide_type = slide["slide_type"]

        if slide_type == "cover":
            img = gen.slide_cover(
                fonts,
                headline=slide["headline"],
                sub=slide["subheadline"],
                slide_n=slide_num,
                total=total_slides
            )
        elif slide_type == "content":
            img = gen.slide_content(
                fonts,
                label=slide["label"],
                headline=slide["headline"],
                body=slide.get("story", ""),
                accent_stat=slide.get("accent_stat", ""),
                accent_label=slide.get("accent_label", ""),
                source=slide.get("source", ""),
                link=slide.get("link", ""),
                chart=slide.get("chart"),
                slide_n=slide_num,
                total=total_slides
            )
        elif slide_type == "cta":
            # Render CTA slide
            img = gen.gradient_bg(top=gen.DARK_SURF, bottom=gen.DEEP_NAVY)
            draw = ImageDraw.Draw(img)

            # Headline
            draw.text((gen.W // 2, 280), slide["headline"],
                     font=fonts["display_md"],
                     fill=gen.WARM_CREAM, anchor="mm")

            # Body lines
            y = 420
            for line in slide.get("body_lines", []):
                draw.text((gen.W // 2, y), line,
                         font=fonts["body_md"],
                         fill=gen.MUTED_CREAM, anchor="mm")
                y += 60

            # CTA button text (simulated)
            y += 80
            draw.rectangle(
                [(gen.W // 2 - 200, y), (gen.W // 2 + 200, y + 60)],
                fill=gen.SOFT_GOLD,
                outline=gen.SOFT_GOLD
            )
            draw.text((gen.W // 2, y + 30), json_data.get("cta_text", "daanaa.org"),
                     font=fonts["body_md"],
                     fill=gen.DEEP_NAVY, anchor="mm")

            # Counter, footer, and logo
            gen.logo_stamp(img)
            gen.footer_url(draw, fonts)
            gen.slide_counter(draw, fonts, slide_num, total_slides)
        else:
            raise ValueError(f"Unknown slide type: {slide_type}")

        page = slide_num - 1

        # Per slide clickable regions (image pixel coords)
        if slide_type == "content" and slide.get("link"):
            url = slide["link"]
            if not url.startswith("http"):
                url = f"https://{url}"
            # "See the data → ..." line sits at (56, H-150), label font is 22px
            link_annots.append((page, (56, gen.H - 160, 700, gen.H - 115), url))
        if slide_type == "cta":
            # Gold button: [80, H-360, W-80, H-240]
            link_annots.append((page, (80, gen.H - 360, gen.W - 80, gen.H - 240),
                                "https://www.daanaa.org"))
        # Footer www.daanaa.org on every slide that draws it
        if slide_type != "cta":
            link_annots.append((page, (gen.W // 2 - 130, gen.H - 55, gen.W // 2 + 130, gen.H - 10),
                                "https://www.daanaa.org"))

        slides.append(img)

    pdf_path = output_dir / f"daanaa_{json_data['carousel_type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    if slides:
        # Convert slides to RGB (PDF requires RGB, not RGBA)
        rgb_slides = []
        for slide in slides:
            if slide.mode != 'RGB':
                rgb_slide = Image.new('RGB', slide.size, (255, 255, 255))
                rgb_slide.paste(slide, mask=slide.split()[-1] if slide.mode == 'RGBA' else None)
                rgb_slides.append(rgb_slide)
            else:
                rgb_slides.append(slide)

        # Save as multi-page PDF using PIL
        rgb_slides[0].save(
            str(pdf_path),
            format="PDF",
            save_all=True,
            append_images=rgb_slides[1:] if len(rgb_slides) > 1 else [],
            duration=0,
            loop=0
        )

        # Make the printed URLs genuinely clickable (PDF link annotations)
        if link_annots:
            _add_link_annotations(pdf_path, link_annots)

    return pdf_path


def _add_link_annotations(pdf_path, annots):
    """Overlay URI link annotations. Image coords are top-left origin;
    PDF coords are bottom-left, and PIL writes pages at 1px = 1pt."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.annotations import Link

    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    writer.append(reader)

    page_h = float(reader.pages[0].mediabox.height)
    for page_idx, (x0, y0, x1, y1), url in annots:
        rect = (x0, page_h - y1, x1, page_h - y0)
        writer.add_annotation(page_number=page_idx, annotation=Link(rect=rect, url=url))

    with open(pdf_path, "wb") as f:
        writer.write(f)

def main():
    parser = argparse.ArgumentParser(description="Render Daanaa carousels from JSON")
    parser.add_argument("json_files", nargs="+", help="JSON carousel files to render")
    parser.add_argument("--output", "-o", help="Output directory (default: scripts/linkedin/output)")
    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else None

    for json_file in args.json_files:
        filepath = Path(json_file)
        if not filepath.exists():
            print(f"❌ Not found: {filepath}")
            continue

        try:
            print(f"Loading: {filepath}")
            data = load_carousel_json(filepath)

            print(f"  Type: {data['carousel_type']}")
            print(f"  Title: {data['title']}")
            print(f"  Slides: {len(data['slides'])}")

            pdf_path = render_carousel_from_json(data, output_dir)
            print(f"✅ Rendered: {pdf_path}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")
            continue

if __name__ == "__main__":
    main()
