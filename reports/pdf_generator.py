from flask import render_template
from datetime import datetime
import os


def generate_pdf_report(case, posts, results_data, output_path):
    """
    Generate a PDF report using WeasyPrint.
    results_data: dict containing all module results.
    """
    try:
        from weasyprint import HTML, CSS

        html_content = render_template(
            'reports/full_report.html',
            case=case,
            posts=posts,
            results=results_data,
            generated_at=datetime.utcnow().strftime('%d %B %Y, %H:%M UTC'),
        )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=[
                CSS(string=_report_css())
            ]
        )
        return True, output_path

    except ImportError:
        return False, "WeasyPrint not installed. Run: pip install weasyprint"
    except Exception as e:
        return False, str(e)


def _report_css():
    """Minimal CSS for clean PDF rendering."""
    return """
        @page {
            margin: 20mm 15mm;
            @top-center {
                content: "PulseIQ — Social Media Analytics Report";
                font-size: 10px;
                color: #666;
            }
            @bottom-right {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10px;
                color: #666;
            }
        }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
            color: #1a1a2e;
            line-height: 1.6;
        }
        h1 { font-size: 22px; color: #0d1117; border-bottom: 2px solid #00d4ff;
             padding-bottom: 8px; margin-bottom: 16px; }
        h2 { font-size: 16px; color: #0d1117; margin-top: 24px;
             border-left: 4px solid #00d4ff; padding-left: 10px; }
        h3 { font-size: 13px; color: #333; margin-top: 16px; }
        table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 10px; }
        th { background: #0d1117; color: #fff; padding: 8px 10px; text-align: left; }
        td { padding: 6px 10px; border-bottom: 1px solid #e0e0e0; }
        tr:nth-child(even) td { background: #f8f9fa; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 99px;
                 font-size: 10px; font-weight: 600; }
        .badge-green  { background: #d4edda; color: #155724; }
        .badge-red    { background: #f8d7da; color: #721c24; }
        .badge-blue   { background: #cce5ff; color: #004085; }
        .badge-yellow { background: #fff3cd; color: #856404; }
        .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
                    margin: 16px 0; }
        .kpi-box  { border: 1px solid #dee2e6; border-radius: 8px; padding: 12px;
                    text-align: center; }
        .kpi-num  { font-size: 22px; font-weight: 700; color: #0d1117; }
        .kpi-lbl  { font-size: 10px; color: #666; margin-top: 4px; }
        .page-break { page-break-before: always; }
        .cover    { text-align: center; padding: 60px 0; }
        .cover h1 { font-size: 32px; border: none; }
        .cover .sub { font-size: 14px; color: #666; margin-top: 8px; }
        .section-divider { border: none; border-top: 1px solid #dee2e6;
                           margin: 20px 0; }
    """
