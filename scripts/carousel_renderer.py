"""
Carousel Rendering Engine
Converts campaign JSON to LinkedIn-ready carousel posts
No external APIs — renders locally
"""

import json
from typing import Dict, List
from datetime import datetime

class CarouselRenderer:
    """Renders campaign carousels to LinkedIn-ready format"""

    def __init__(self, campaign: Dict):
        self.campaign = campaign
        self.id = campaign.get('id')
        self.title = campaign.get('title')
        self.slides = campaign.get('slides', [])

    def render_linkedin_caption(self) -> str:
        """
        Render LinkedIn post caption (text-only, no carousel markup)
        Includes hashtags and CTA
        """
        caption_parts = []

        # Hook/headline
        first_slide = next((s for s in self.slides if s.get('slide_type') == 'cover'), None)
        if first_slide:
            caption_parts.append(first_slide.get('headline', ''))

        # Body from first content slide
        first_content = next((s for s in self.slides if s.get('slide_type') == 'content'), None)
        if first_content:
            caption_parts.append('')  # Line break
            caption_parts.append(first_content.get('story', ''))

        # Hashtags
        caption_parts.append('')  # Line break
        hashtags = [
            '#FindYourCause',
            '#NonprofitDiscovery',
            '#Giving',
            '#Daanaa'
        ]
        caption_parts.append(' '.join(hashtags))

        # CTA slide
        cta_slide = next((s for s in self.slides if s.get('slide_type') == 'cta'), None)
        if cta_slide:
            caption_parts.append('')
            caption_parts.append(cta_slide.get('headline', ''))

        return '\n'.join(caption_parts)

    def render_slide_html(self, slide: Dict, slide_number: int) -> str:
        """
        Render individual slide as HTML
        Designed for LinkedIn carousel display
        """
        slide_type = slide.get('slide_type')

        if slide_type == 'cover':
            return self._render_cover_slide(slide, slide_number)
        elif slide_type == 'content':
            return self._render_content_slide(slide, slide_number)
        elif slide_type == 'cta':
            return self._render_cta_slide(slide, slide_number)
        else:
            return self._render_default_slide(slide, slide_number)

    def _render_cover_slide(self, slide: Dict, num: int) -> str:
        """Cover slide (title slide)"""
        return f"""
        <div class="carousel-slide cover-slide" data-slide="{num}">
            <div class="slide-bg gradient-primary"></div>
            <div class="slide-content">
                <div class="slide-number">{num}/8</div>
                <h1 class="headline">{slide.get('headline', '')}</h1>
                <p class="subheadline">{slide.get('subheadline', '')}</p>
                {''.join([
                    f'<div class="accent-stat"><strong>{slide.get("accent_stat", "")}</strong></div>',
                    f'<div class="accent-label">{slide.get("accent_label", "")}</div>'
                ])}
            </div>
        </div>
        """

    def _render_content_slide(self, slide: Dict, num: int) -> str:
        """Content slide (body content)"""
        stats_html = ''
        if slide.get('stats'):
            stats_html = '<div class="stats-grid">'
            for stat in slide['stats']:
                stats_html += f"""
                <div class="stat-item">
                    <p class="stat-label">{stat.get('label', '')}</p>
                    <p class="stat-value">{stat.get('value', '')}</p>
                </div>
                """
            stats_html += '</div>'

        pull_quote_html = ''
        if slide.get('pull_quote'):
            pull_quote_html = f"""
            <blockquote class="pull-quote">
                {slide.get('pull_quote', '')}
            </blockquote>
            """

        return f"""
        <div class="carousel-slide content-slide" data-slide="{num}">
            <div class="slide-header">
                <span class="slide-label">{slide.get('label', '')}</span>
                <div class="slide-number">{num}/8</div>
            </div>
            <h2 class="headline">{slide.get('headline', '')}</h2>
            <p class="story">{slide.get('story', '')}</p>
            {stats_html}
            {pull_quote_html}
            <footer class="slide-footer">
                <p class="source">{slide.get('source', '')}</p>
            </footer>
        </div>
        """

    def _render_cta_slide(self, slide: Dict, num: int) -> str:
        """Call-to-action slide (final slide)"""
        body_lines = '</li><li>'.join(slide.get('body_lines', []))
        return f"""
        <div class="carousel-slide cta-slide" data-slide="{num}">
            <div class="slide-bg gradient-accent"></div>
            <div class="slide-content">
                <h1 class="headline">{slide.get('headline', '')}</h1>
                <ul class="cta-list">
                    <li>{body_lines}</li>
                </ul>
                <p class="cta-footer">daanaa.org</p>
            </div>
        </div>
        """

    def _render_default_slide(self, slide: Dict, num: int) -> str:
        """Default slide renderer"""
        return f"""
        <div class="carousel-slide default-slide" data-slide="{num}">
            <div class="slide-number">{num}</div>
            <h2>{slide.get('headline', '')}</h2>
            <p>{slide.get('story', '')}</p>
        </div>
        """

    def render_full_carousel_html(self) -> str:
        """Render complete carousel HTML (for preview/archiving)"""
        slides_html = ''
        for i, slide in enumerate(self.slides, 1):
            slides_html += self.render_slide_html(slide, i)

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{self.title}</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .carousel-container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
                .carousel-slide {{
                    background: white;
                    border-radius: 12px;
                    padding: 40px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    page-break-inside: avoid;
                }}
                .cover-slide {{ background: linear-gradient(135deg, #0A1628 0%, #1a3a52 100%); color: white; }}
                .cta-slide {{ background: linear-gradient(135deg, #D4B968 0%, #e6ccb3 100%); }}
                .headline {{ font-size: 32px; font-weight: bold; margin-bottom: 12px; }}
                .subheadline {{ font-size: 18px; margin-bottom: 20px; opacity: 0.9; }}
                .accent-stat {{ font-size: 48px; font-weight: bold; color: #D4B968; }}
                .accent-label {{ font-size: 14px; opacity: 0.8; margin-top: 8px; }}
                .story {{ font-size: 16px; line-height: 1.6; margin-bottom: 20px; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px; }}
                .stat-item {{ background: #f5f5f5; padding: 12px; border-radius: 8px; }}
                .stat-label {{ font-size: 12px; color: #666; margin-bottom: 4px; }}
                .stat-value {{ font-size: 20px; font-weight: bold; }}
                .pull-quote {{
                    background: #f5f5f5;
                    padding: 16px;
                    border-left: 4px solid #D4B968;
                    font-style: italic;
                    margin: 16px 0;
                }}
                .slide-label {{ font-size: 12px; font-weight: bold; color: #D4B968; text-transform: uppercase; }}
                .slide-footer {{ font-size: 12px; color: #999; margin-top: 20px; }}
                .source {{ font-size: 11px; color: #999; }}
                .slide-number {{ font-size: 14px; color: #999; text-align: right; }}
                @media print {{ body {{ background: none; }} }}
            </style>
        </head>
        <body>
            <div class="carousel-container">
                <h1 style="margin-bottom: 20px;">{self.title}</h1>
                {slides_html}
            </div>
        </body>
        </html>
        """

    def to_json(self) -> str:
        """Export carousel as JSON"""
        return json.dumps(self.campaign, indent=2)

    def get_metadata(self) -> Dict:
        """Get carousel metadata for tracking"""
        return {
            'id': self.id,
            'title': self.title,
            'carousel_type': self.campaign.get('carousel_type'),
            'slide_count': len(self.slides),
            'cta_text': self.campaign.get('cta_text', ''),
            'target_audience': self.campaign.get('target_audience', ''),
            'hashtags': ['#FindYourCause', '#NonprofitDiscovery', '#Giving', '#Daanaa'],
        }


def load_carousel_from_file(filepath: str) -> CarouselRenderer:
    """Load carousel JSON and initialize renderer"""
    with open(filepath, 'r') as f:
        carousel_data = json.load(f)
    return CarouselRenderer(carousel_data)


if __name__ == '__main__':
    # Test rendering
    import sys
    if len(sys.argv) > 1:
        renderer = load_carousel_from_file(sys.argv[1])
        print('Carousel Metadata:')
        print(json.dumps(renderer.get_metadata(), indent=2))
        print('\nLinkedIn Caption:')
        print(renderer.render_linkedin_caption())
